import numpy as np
from typing import Optional, cast
from scipy.integrate._ivp.ivp import OdeResult
from typing import Dict, Tuple
from scipy.integrate import solve_ivp
from ..params.parameters import create_default_parameters

class GasSwellingModel:
    """气体肿胀模型,实现公式1-25的数值求解, Ncb, Ncf 作为状态变量"""

    def __init__(self, params: Optional[Dict] = None):
        """初始化模型参数"""
        self.params = params if params else create_default_parameters()
        self.params.setdefault('Zvc', 1.0) # Cavity bias for vacancy (Not directly used if R is not state var)
        self.params.setdefault('Zic', 1.0) # Cavity bias for interstitial (Not directly used if R is not state var)
        self.initial_state = self._initialize_state()
        self.debug_history = {
            'time': [], 'Rcb': [], 'Rcf': [], 'Ncb': [], 'Ncf': [], 
            'Pg_b': [], 'Pg_f': [], 'swelling': [],
            'Pext_b': [], 'Pext_f': [], 
            'cv_star_b': [], 'cv_star_f': [], 
            'dRcb_dt': [], 'dRcf_dt': [],
            'dCgb_dt': [], 'dCgf_dt': []
        }
        self.step_count = 0
        self.solver_success = True # Initialize solver status flag
        self.current_time = 0.0
        # 添加CSV调试输出文件
        self.debug_csv_path = 'debug_output.csv'
        self.debug_csv_header_written = False

            
    def _calculate_cv0(self) -> float:
        """计算无缺陷时的热平衡空位浓度(公式16)"""
        T = self.params['temperature']
        C = self.params['Evf_coeffs']
        Evf =( C[0] + C[1]*T)*self.params['Evfmuti']
        exponent_arg = -Evf / (self.params['kB_ev'] * T)
        exponent_arg = np.clip(exponent_arg, -700, 700) 
        cv0 = np.exp(exponent_arg)
        return cv0

    def _calculate_ci0(self) -> float:
        """计算无缺陷时的热平衡间隙原子浓度"""
        T = self.params['temperature']
        C = self.params['Eif_coeffs']
        Eif = C[0] + C[1]*T + C[2]*T**2 + C[3]*T**3
        exponent_arg = -Eif / (self.params['kB_ev'] * T)
        exponent_arg = np.clip(exponent_arg, -700, 700)
        ci0 = np.exp(exponent_arg)
        return ci0


    # --- Helper functions below now calculate R from N when needed ---



    def _gas_influx(self, Cgb: float, Cgf: float) -> float:
        """计算从基体扩散到相界面的气体原子通量(公式2)"""
        #return (6.0 / self.params['grain_diameter']) * self.params['Dgb'] * Cgb
        return (12.0 /( self.params['grain_diameter'])**2) * self.params['Dgb'] * (Cgb-Cgf)
    
    def _calculate_gas_release_rate(self, Cgf: float, Ccf: float, Rcf: float, Ncf: float) -> float:
        """计算气体释放率(公式9-12)"""
        from scipy.stats import norm
        # geometric factor
        theta = 50/180* np.pi
        ff_theta = 1 - 1.5 * np.cos(theta) + 0.5 * np.cos(theta) **3
        Af = np.pi * Rcf**2 * Ccf * ff_theta  # Eq.10
        Sv_aa = 6.0 / self.params['grain_diameter']  # grain-face area per unit volume, m-1
        Af_max = 0.907 * Sv_aa  # Eq.11
        
        Af_ratio = Af / Af_max
        
        # 计算腔室互连系数 (Eq.12)
        if Af_ratio <= 0.25:
            chi = 0.0
        elif Af_ratio >= 1.0:
            chi = 1.0 
        else:
            chi = Af_ratio
        
        # 重构计算公式增强数值稳定性
        h0 = chi * (Cgf + Ccf * Ncf)
        return h0
    def _calculate_idealgas_pressure(self, Rc: float, Nc: float) -> float:
        """使用理想气体状态方程简化版计算气体压力"""
        if Rc <= 1e-12 or Nc <= 0: return 0.0
        T = self.params['temperature']
        kB = self.params['kB']
        return 3* Nc* kB * T / (4 * np.pi * Rc**3)
        
    def _calculate_modifiedvongas_pressure(self, Rc: float, Nc: float) -> float:
        """使用修正的范德瓦尔气体状态方程计算气体压力"""
        if Rc <= 1e-12 or Nc <= 0: return 0.0
        T = self.params['temperature']
        kB = self.params['kB']
        hs=0.6
        bv=8.5e-29
        return Nc* kB * T / (4/3 * np.pi * Rc**3-Nc* hs* bv)   

    def _calculate_VirialEOSgas_pressure(self, Rc: float, Nc: float) -> float:
        """使用_VirialEOS气体状态方程计算气体压力"""
        if Rc <= 1e-12 or Nc <= 0: return 0.0
        R = self.params['R']
        T = self.params['temperature']
        nu = 4/3 * np.pi * 1e6 * Rc**3 / Nc * 6.02214076e23 #Rc单位换成cm
        b0 = 197.229
        b1 = 120307.145
        b2 = 60.555
        c0 = -22038.723
        c1 = 2292.793
        c2 = -117.564
        d0 = 1030015.045
        d1 = -5.200
        d2 = -280.677
        Bs = b0 + b1/T +b2/T**2
        Cs = c0 + c1/T +c2/T**2
        Ds = d0 + d1/T +d2/T**2

        return R * T * (1.0 + Bs/nu + Cs/nu**2 + Ds/nu**3)/nu       
        
    def _calculate_ronchi_pressure(self, Rc: float, Nc: float, T: float) -> float:
        """使用 Ronchi 硬球模型计算气体压力 (公式 27-33),
        Precipitation kinetics of rare gases implanted into metals,JNM 1992"""
        # (Implementation remains the same as before)
        if Rc <= 1e-12 or Nc <= 0: return 0.0
        # T = self.params['temperature']
        R = self.params['R']
        Mass = self.params['xe_mass'] # 摩尔质量, kg/mol
        Av = self.params['Av']
        sigma = self.params['xe_sigma']
        Tc = self.params['xe_Tc']
        dc = self.params['xe_dc']
        Vc = self.params['xe_Vc']
        q_coeffs = self.params['xe_q_coeffs']
        V_bubble = (4.0/3.0) * np.pi * Rc**3 # bubble volume
        di = Nc * Mass / ( V_bubble * Av ) # gas density, kg/m3
        Tr = T / Tc # reduced temperature        
        # if Tr <= 1e-6: Tr = 1e-6
        T1 = Tr**(5.0/7.0)
        dr = di / dc # reduced density
        # calculation of B_plus, Eq.31
        denom_B = ((T1 - 0.553) * T1) * Tr**0.25
        # if abs(denom_B) < 1e-15: B_plus = 0.0
        B_plus = 1.843 * (1.0 - 1.078 * (T1 - 0.162)) / denom_B
        # calculation of f_T, Eq.29
        beta = 1.0 / T
        f_T = 0.0
        for n in range(len(q_coeffs)): f_T += (beta**(n+1)) * q_coeffs[n]**(n+1)
        # Eq.30, effective volume of the gas, v
        v0 = (4.0/3.0) * np.pi * Av * sigma**3 
        v = v0 * (B_plus + f_T)
        # Eq.27, hard sphere model parameter Zhs by Camaham and Starling
        yi = v * di / 4.0
        # if yi >= 1.0: yi = 0.99999
        denom_Zhs = (1.0 - yi)**3
        # if abs(denom_Zhs) < 1e-15: Zhs = 1e9
        Zhs = (1.0 + yi - yi**2 - yi**3) / denom_Zhs
        
        term_Ax = 1.538 / Tr
        Ax = 0.615 * (term_Ax**4) * (term_Ax - 1.0) 
        Delta_Z = dr**2 * ((dr / Tr) * (7.0 * dr - 1.33/Tr) + Ax * (1.0 + dr**3)) # Eq.33
        Pg = (Zhs - di * v0 * f_T - Delta_Z) * R * T / V_bubble # Eq.27
        print ("fenmu:", Zhs - di * v0 * f_T - Delta_Z, V_bubble)
        return max(Pg, 0.0)

    # Note: _calculate_thermal_vacancy_concentration is NOT directly used in ODEs if R is not a state variable.
    # It's only needed if we were calculating dR/dt explicitly.

    # Note: _calculate_cavity_growth_rate is NOT needed if R is not a state variable.
    def _initialize_state(self) -> np.ndarray:
        """初始化状态变量, Ncb, Ncf included, Rcb, Rcf removed"""
        Nc_init = 5.0 # 初始气泡内气体数, atoms
        Cg_init = 0.0 # 初始气体浓度, atoms/m3
        Cc_init = 0.0  # 初始气腔浓度, cavities/m3
        R_init = 1e-8 # 初始半径,形核的临界半径,假设初始气泡半径大于临界形核半径，如10nm
        cv0 = self._calculate_cv0() 
        ci0 = self._calculate_ci0() 
        kv_param = self.params['kv_param']
        ki_param = self.params['ki_param']

        # State vector: [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cv, ci, released_gas] - 11 variables
        return np.array([
            Cg_init,     # 0: Cgb
            Cc_init,     # 1: Ccb
            Nc_init,  # 2: Ncb (Initial atoms per bulk bubble)
            R_init,   # 3: Rcb (Initial radius of bulk bubble)
            Cg_init,  # 4: Cgf
            Cc_init,  # 5: Ccf
            Nc_init,  # 6: Ncf (Initial atoms per boundary bubble)
            R_init,   # 7: Rcf (Initial radius of boundary bubble)
            cv0,   # 8: cvb
            ci0,   # 9: cib
            kv_param,  # 10: kvb
            ki_param,  # 11: kib
            cv0,   # 12: cvf
            ci0,   # 13: cif
            kv_param,  # 14: kvf
            ki_param,  # 15: kif
            0.0    # 16: released_gas
        ])

        
    def _equations(self, t: float, state: np.ndarray) -> np.ndarray:
        """定义微分方程组(公式1-25)"""
        # 更新当前时间
        self.current_time = t
        # Unpack state vector (13 variables)
        Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvb, cib, kvb, kib, cvf, cif, kvf, kif, released_gas = state

        # 数值保护：避免半径为零或过大
        Rcb_safe = np.clip(Rcb, 5e-10, 1e-4)
        Rcf_safe = np.clip(Rcf, 5e-10, 1e-4)
        T = self.params['temperature']
        # Calculate diffusivities of point defects and gas atoms in bulk and phase boundary
        kB_ev = self.params['kB_ev']
        T = self.params['temperature']
        Dv = self.params['Dv0'] * np.exp(-self.params['Evm'] / (kB_ev * T))
        Di = self.params['Di0'] * np.exp(-self.params['Eim'] / (kB_ev * T))
        
        Dgb = self.params['Dgb_prefactor'] * np.exp(-self.params['Dgb_activation_energy'] / (kB_ev * T)) \
            + self.params['Dgb_fission_term'] * self.params['fission_rate']
            
        Dgf = self.params['Dgf_multiplier'] * Dgb

        # 点缺陷计算(公式17-24) 
        Zv = self.params['Zv']
        Zi = self.params['Zi']
        rho = self.params['dislocation_density']

        # 位错汇聚强度 (公式 23,24)
        k_vd2 = Zv * rho
        k_id2 = Zi * rho
        
        kvb = 2 * np.pi*Rcb_safe**2*Ccb*np.sqrt(4*np.pi*np.pi*Rcb_safe**4*Ccb**2+4 * np.pi * Rcb_safe * Ccb+k_vd2) 
        kib = 2 * np.pi*Rcb_safe**2*Ccb*np.sqrt(4*np.pi*np.pi*Rcb_safe**4*Ccb**2+4 * np.pi * Rcb_safe * Ccb+k_id2)   
        kvf = 2 * np.pi*Rcf_safe**2*Ccf*np.sqrt(4*np.pi*np.pi*Rcf_safe**4*Ccf**2+4 * np.pi * Rcf_safe * Ccf+k_vd2)     
        kif = 2 * np.pi*Rcf_safe**2*Ccf*np.sqrt(4*np.pi*np.pi*Rcf_safe**4*Ccf**2+4 * np.pi * Rcf_safe * Ccf+k_id2)        
        # 公式21和22,计算基体和界面空腔对点缺陷的汇聚强度
        kvc2_b = 4 * np.pi * Rcb_safe * Ccb * (1 + kvb * Rcb_safe)
        kic2_b = 4 * np.pi * Rcb_safe * Ccb * (1 + kib * Rcb_safe)
        kvc2_f = 4 * np.pi * Rcf_safe * Ccf * (1 + kvf * Rcf_safe)
        kic2_f = 4 * np.pi * Rcf_safe * Ccf * (1 + kif * Rcf_safe)
        # Total sink strengths, 公式 19, 20
        kvb2_total = kvc2_b + k_vd2
        kib2_total = kic2_b + k_id2
        kvf2_total = kvc2_f + k_vd2
        kif2_total = kic2_f + k_id2
        # Square roots,避免负数开方
#        kvb = np.sqrt(np.maximum(kvb2_total, 0.0))
#        kib = np.sqrt(np.maximum(kib2_total, 0.0))
#        kvf = np.sqrt(np.maximum(kvf2_total, 0.0))
#        kif = np.sqrt(np.maximum(kif2_total, 0.0))

        # 基体和晶界处的点缺陷浓度 (dcv/dt, dci/dt - 公式 17, 18)
        # 间隙与空位复合因子
        alpha = 4 * np.pi * self.params['recombination_radius'] * (Dv + Di)/self.params['Omega']
        phi =  self.params['fission_rate']* self.params['displacement_rate']
        # 基体
        # 空位扩散项
        term2_dcvb = kvb2_total * Dv * cvb
        # 空位-间隙复合项
        term3_dcvb = alpha * cvb * cib
        dcvb_dt = phi - kvb2_total * Dv * cvb - alpha * cvb * cib
        # 空位扩散项
        term2_dcib = kib2_total * Di * cib
        # 空位-间隙复合项
        term3_dcib = alpha * cvb * cib
        dcib_dt = phi - kib2_total * Di * cib - alpha * cvb * cib
        # 晶界
        dcvf_dt = phi - kvf2_total * Dv * cvf - alpha * cvf * cif
        dcif_dt = phi - kif2_total * Di * cif - alpha * cvf * cif
        # 计算空腔附近的空位浓度 （公式15）
        cv0 = self._calculate_cv0()
        kB_J = self.params['kB']

        # 计算空腔中的气压 $P_g$,最小值为1Pa
        Pg_b = max (self._calculate_VirialEOSgas_pressure(Rcb_safe, Ncb),1.0)
        # Pg_b_Ronchi =  max (self._calculate_ronchi_pressure(Rcb_safe, Ncb),1.0)
        # Pg_b_ratio = Pg_b / Pg_b_Ronchi
        Pg_f = max (self._calculate_VirialEOSgas_pressure(Rcf_safe, Ncf),1.0)
        
        gamma = self.params['surface_energy']
        sigma_ext = self.params['hydrastatic_pressure']
        # 气压差 = 内压 - 表面张力 - 静水压
        # 气压
        # Pextb_term1 = Pg_b
        #表面张力,在初期Rc过小可能导致指数项过大,即热平衡空位浓度过高
        Pextb_term2 = 2*gamma/Rcb_safe/Pg_b
        #静水压
        Pextb_term3 = sigma_ext/Pg_b
        Pext_b = Pg_b - 2*gamma/Rcb_safe - sigma_ext
        Pext_f = Pg_f - 2*gamma/Rcf_safe - sigma_ext
        # Pext_f = Pg_f - 2*gamma/Rcf_safe
        # 指数项
        arg_factor =  self.params['Omega'] / (kB_J * T)
        arg_b = - Pext_b * self.params['Omega'] / (kB_J * T)
        arg_f = - Pext_f * self.params['Omega'] / (kB_J * T)
        # 分别计算基体和界面的空腔附近空位浓度$c_v^*$
        cv_star_b = cv0 * np.exp(np.clip(arg_b, -700, 700))
        cv_star_f = cv0 * np.exp(np.clip(arg_f, -700, 700))


        # 公式14
        # 空位被空腔吸收
        # dRcb_term1 = kvc2_b*Dv*cvb
        # 间隙原子被空腔吸收
        dRcb_term2 = kic2_b*Di*cib / (kvc2_b*Dv*cvb)
        # 空位发射
        dRcb_term3 = cv_star_b / cvb
        # dRcb_dt = (1/(4*np.pi*Rcb_safe**2*Ccb)) * (kvc2_b*Dv*cvb - kic2_b*Di*cib - kvc2_b*Dv*cv_star_b)
        dRcb_dt = (1/(4*np.pi*Rcb_safe**2*Ccb)) * kvc2_b*Dv*cvb * (1 - dRcb_term2 - dRcb_term3)
        
        # dRcf_term1 = kvc2_f*Dv*cvf
        dRcf_term2 = kic2_f*Di*cif / (kvc2_f*Dv*cvf)
        dRcf_term3 = cv_star_f / cvf
        dRcf_dt = (1/(4*np.pi*Rcf_safe**2*Ccf)) * kvc2_f*Dv*cvf * (1 - dRcf_term2 - dRcf_term3)
#        min_radius = 2e-10
#        if Rcb <= min_radius and dRcb_dt < 0:
#            dRcb_dt = 0
#        if Rcf <= min_radius and dRcf_dt < 0:
#            dRcf_dt = 0
        # 从基体扩散到相界面的气体通量
        g0 = self._gas_influx(Cgb, Cgf)
        h0 = self._calculate_gas_release_rate(Cgf, Ccf, Rcf_safe, Ncf) # Pass Ncf
        #h0 = 0 # testing, no gas release


        # 公式13
        dNcf_dt = 4 * np.pi * Rcf_safe * Dgf * Cgf - h0 * Ncf

        # 基体中气体原子浓度变化速率 (dCgb/dt - 公式 1)
        # 气泡形核吸收项
        term1_Cgb = -16 * np.pi * self.params['Fnb'] * self.params['Xe_radii'] * Dgb * Cgb**2
        # 气体原子扩散吸收项
        term2_Cgb = -4 * np.pi * Rcb_safe * Dgb * Cgb * Ccb
        # 气体原子迁移到晶界
        term3_Cgb = -g0
        # 裂变产生的气体原子
        term4_Cgb = self.params['gas_production_rate'] * self.params['fission_rate']
        # 气泡气体原子重溶
        term5_Cgb = self.params['resolution_rate'] * Ccb * Ncb
        dCgb_dt = term1_Cgb + term2_Cgb + term3_Cgb + term4_Cgb + term5_Cgb

        # 基体气泡浓度变化速率 (dCcb/dt - 公式 3)
        Ncb_safe_denom = max(Ncb, 2)
        dCcb_dt = (16 * np.pi * self.params['Fnb'] * self.params['Xe_radii'] * Dgb * Cgb**2) / Ncb_safe_denom

        # 每个空腔内气体原子数变化速率 (dNcb/dt - 公式 5)
        # 从基体扩散到空腔的气体原子速率
        term1_Ncb = 4 * np.pi * Rcb_safe * Dgb * Cgb
        term2_Ncb = self.params['resolution_rate'] * Ncb
        ratio_Ncb = term1_Ncb/term2_Ncb
        dNcb_dt = term1_Ncb - self.params['resolution_rate'] * Ncb

        # 晶界气体浓度,个/m3 (dCgf/dt - 公式 6)
        # 气体原子形核吸收项
        term1_Cgf = -16 * np.pi * self.params['Fnf'] * self.params['Xe_radii'] * Dgf * Cgf**2
        # 气体原子扩散吸收项
        term2_Cgf = -4 * np.pi * Rcf_safe * Dgf * Cgf * Ccf
        # 从基体迁移到晶界的气体原子
        term3_Cgf = g0
        # 气体原子在晶界释放
        term4_Cgf = h0 * Cgf
        # 公式 6: - 气泡连通释放 h0 * Cgf term
        dCgf_dt = term1_Cgf + term2_Cgf + term3_Cgf - term4_Cgf

        # 晶界空腔浓度=晶界形核吸收气体原子 / 每个空腔气体原子数 (dCcf/dt - 公式 7)
        Ncf_safe_denom = max(Ncf, 2)
        dCcf_dt = (16 * np.pi * self.params['Fnf'] * self.params['Xe_radii'] * Dgf * Cgf**2) / Ncf_safe_denom


        # Cumulative gas release rate (dh_dt)
        dh_dt = h0

        # 修正导数数组维度并增强数值稳定性 (确保17个元素)
        derivatives = np.array([
            np.clip(dCgb_dt, -1e20, 1e20),    # 0: Cgb
            np.clip(dCcb_dt, -1e20, 1e20),    # 1: Ccb
            np.clip(dNcb_dt, -1e8, 1e8),    # 2: Ncb
            np.clip(dRcb_dt, 0, 1e5),    # 3: Rcb
            np.clip(dCgf_dt, -1e20, 5e20),    # 4: Cgf
            np.clip(dCcf_dt, -1e20, 5e20),    # 5: Ccf
            np.clip(dNcf_dt, -1e8, 1e8),    # 6: Ncf
            np.clip(dRcf_dt, 0, 1e5),    # 7: Rcf
            np.clip(dcvb_dt, -1e8, 5e20),    # 8: cvb
            np.clip(dcib_dt, -1e8, 5e20),    # 9: cib
            0.0,  #13: kvb导数 (参数保持不变)
            0.0,  #14: kib导数 (参数保持不变)
            np.clip(dcvf_dt, -1e8, 1e8),    #10: cvf
            np.clip(dcif_dt, -1e8, 1e8),    #11: cif
            0.0,  #15: kvf导数 (参数保持不变)
            0.0,   #16: kif导数 (参数保持不变)
            np.clip(dh_dt, -1e5, 1e5)      #12: released_gas
        ])
#        derivatives = np.nan_to_num(derivatives, nan=0.0, posinf=1e10, neginf=-1e10)
        derivatives = np.array(derivatives)
        derivatives = np.where(np.isnan(derivatives), 0.0, derivatives)
        derivatives = np.where(np.isinf(derivatives), 1e10 * np.sign(derivatives), derivatives)
        # 增加步数计数器
        self.step_count += 1


#    def _record_debug(self, t: float, state: np.ndarray, Pg_b: float, Pg_f: float,
#                     Pext_b: float, Pext_f: float, cv_star_b: float, cv_star_f: float,
#                     dRcb_dt: float, dRcf_dt: float, dCgb_dt: float, dCgf_dt: float):
#        """记录调试信息"""
#        # 解包状态变量
#        Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvb, cib, kvb, kib, cvf, cif, kvf, kif, released_gas = state
#        
        # 计算肿胀率
        V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
        swelling = (V_bubble_b + V_bubble_f) * 100  # 肿胀率（百分比）
        
        # 记录调试信息
        self.debug_history['time'].append(t)
        self.debug_history['Rcb'].append(Rcb)
        self.debug_history['Rcf'].append(Rcf)
        self.debug_history['Ncb'].append(Ncb)
        self.debug_history['Ncf'].append(Ncf)
        self.debug_history['Pg_b'].append(Pg_b)
        self.debug_history['Pg_f'].append(Pg_f)
        self.debug_history['swelling'].append(swelling)
        self.debug_history['Pext_b'].append(Pext_b)
        self.debug_history['Pext_f'].append(Pext_f)
        self.debug_history['cv_star_b'].append(cv_star_b)
        self.debug_history['cv_star_f'].append(cv_star_f)
        self.debug_history['dRcb_dt'].append(dRcb_dt)
        self.debug_history['dRcf_dt'].append(dRcf_dt)
        self.debug_history['dCgb_dt'].append(dCgb_dt)
        self.debug_history['dCgf_dt'].append(dCgf_dt)
        #self._write_debug_to_csv(t, dRcb_term2, cib, cvb, kvc2_b, kic2_b, Di, Dv, Di/Dv)        
        
        return derivatives  
    def _write_debug_to_csv(self, t: float, dRcb_term2: float, cib: float, cvb: float,
                           kvc2_b: float, kic2_b: float, Di: float,
                           Dv: float, DiDv: float):
        """将调试信息写入CSV文件"""
        import csv
        import os
        
        # 创建或追加到CSV文件
        mode = 'a' if os.path.exists(self.debug_csv_path) else 'w'
        
        with open(self.debug_csv_path, mode, newline='') as f:
            writer = csv.writer(f)
            
            # 如果是新文件，写入表头
            if mode == 'w' or not self.debug_csv_header_written:
                writer.writerow([
                    'time', 'dRcb_term2','cib', 'cvb', 'kvc2_b', 
                    'kic2_b', 'Di', 'Dv', 'Di/Dv'
                ])
                self.debug_csv_header_written = True
            
            # 写入数据行
            writer.writerow([
               t, dRcb_term2, cib, cvb, kvc2_b, kic2_b, Di, 
               Dv, DiDv
            ])
      
    def solve(self, t_span: Tuple[float, float] = (0, 7200000),
              t_eval: Optional[np.ndarray] = None,
              dt: float = 1e-9,
              max_dt: float = 100.0,
              max_steps: int = 1000000,
              output_interval: int = 1000) -> Dict:
        """求解微分方程组"""
        self.step_count = 0
        self.debug_interval = output_interval
        
        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)

        # 调整求解器参数并添加异常处理
        try:
            sol = solve_ivp(
                fun=self._equations,
                t_span=t_span,
                y0=np.clip(self.initial_state, 1e-12, 1e30),
                t_eval=t_eval,
                method='BDF',
                rtol=1e-4,
                atol=1e-6,
                first_step=dt,
                max_step=max_dt,
                max_steps=max_steps
            )
            self.solver_success = sol.success
        except Exception as e:
            print(f"Solver error: {str(e)}")
            self.solver_success = False
            sol = type('', (), {})()
            sol.success = False
            sol.t = np.array([])
            sol.y = np.array([])


#        if not sol.success:
#            print(f"Warning: ODE solver failed! Message: {sol.message}")

        # Map results to dictionary (9 state variables)
        results_dict = {
            'time': sol.t,
            'Cgb': sol.y[0],
            'Ccb': sol.y[1],
            'Ncb': sol.y[2],
            'Rcb': sol.y[3],
            'Cgf': sol.y[4],
            'Ccf': sol.y[5],
            'Ncf': sol.y[6],
            'Rcf': sol.y[7],
            'cvb': sol.y[8],
            'cib': sol.y[9],
            'kvb': sol.y[10],
            'kib': sol.y[11],
            'cvf': sol.y[12],
            'cif': sol.y[13],
            'kvf': sol.y[14],
            'kif': sol.y[15],
            'released_gas': sol.y[16]
        }
#        if not sol.success:
#             for key, val in results_dict.items():
#                 if key != 'time' and len(val) != len(sol.t):
#                     padded_val = np.full(len(sol.t), np.nan)
#                     valid_len = len(val)
#                     padded_val[:valid_len] = val
#                     results_dict[key] = padded_val
        # 添加肿胀率计算结果
        Rcb = results_dict['Rcb']
        Rcf = results_dict['Rcf']
        Ccb = results_dict['Ccb']
        Ccf = results_dict['Ccf']
        V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
        results_dict['swelling'] = (V_bubble_b + V_bubble_f) * 100
        return results_dict
    
#    def plot_debug_history(self, save_dir: str = 'debug_plots/'):
#        """绘制并保存调试历史图表"""
#        import os
#        import matplotlib.pyplot as plt
#        
#        if not os.path.exists(save_dir):
#            os.makedirs(save_dir)
#        
#        t = np.array(self.debug_history['time'])
#        fission_density = np.array(t) * 5e19 
#
#        # 绘制半径随时间的变化
#        plt.figure(figsize=(10, 6))
#        plt.plot(t, self.debug_history['Rcb'], label='Rcb')
#        plt.plot(t, self.debug_history['Rcf'], label='Rcf')
#        plt.xlabel("time, s")
#        plt.ylabel("radius,m")
#        plt.title("RADIUS VS TIME")
#        plt.legend()
#        plt.grid(True)
#        plt.savefig(f"{save_dir}/radius_vs_time.png")
#        plt.close()
#        
#        # 绘制压力随时间的变化
#        plt.figure(figsize=(10, 6))
#        plt.plot(t, self.debug_history['Pg_b'], label='Pg_b')
#        plt.plot(t, self.debug_history['Pg_f'], label='Pg_f')
#        plt.xlabel("time, s")
#        plt.ylabel("Pressure, Pa")
#        plt.title("PRESSURE VS TIME")
#        plt.legend()
#        plt.grid(True)
#        plt.savefig(f"{save_dir}/pressure_vs_time.png")
#        plt.close()
#        
#        # 绘制过压随时间的变化
#        plt.figure(figsize=(10, 6))
#        plt.plot(t, self.debug_history['Pext_b'], label='Pext_b')
#        plt.plot(t, self.debug_history['Pext_f'], label='Pext_f')
#        plt.axhline(y=0, color='r', linestyle='--')
#        plt.xlabel("time, s")
#        plt.ylabel("Pressure bias, Pa")
#        plt.title("PRESSURE BIAS VS TIME")
#        plt.legend()
#        plt.grid(True)
#        plt.savefig(f"{save_dir}/excess_pressure_vs_time.png")
#        plt.close()
#        
#        # 绘制热平衡空位浓度随时间的变化
#        plt.figure(figsize=(10, 6))
#        plt.plot(t, self.debug_history['cv_star_b'], label='cv_star_b')
#        plt.plot(t, self.debug_history['cv_star_f'], label='cv_star_f')
#        plt.xlabel("time, s")
#        plt.ylabel("VOID CONCERNTRATION,CM-3")
#        plt.title("VOID CONCERNTRATION VS TIME")
#        plt.legend()
#        plt.grid(True)
#        plt.savefig(f"{save_dir}/cv_star_vs_time.png")
#        plt.close()
#        
#        # 绘制半径变化率随时间的变化
#        plt.figure(figsize=(10, 6))
#        plt.plot(t, self.debug_history['dRcb_dt'], label='dRcb_dt')
#        plt.plot(t, self.debug_history['dRcf_dt'], label='dRcf_dt')
#        plt.axhline(y=0, color='r', linestyle='--')
#        plt.xlabel("time, s")
#        plt.ylabel("Radius change rate, m/s")
#        plt.title("Radius change rate vs time")
#        plt.legend()
#        plt.grid(True)
#        plt.savefig(f"{save_dir}/dR_dt_vs_time.png")
#        plt.close()
#        
#        # 绘制气体浓度变化率随时间的变化
#        plt.figure(figsize=(10, 6))
#        plt.plot(t, self.debug_history['dCgb_dt'], label='dCgb_dt')
#        plt.plot(t, self.debug_history['dCgf_dt'], label='dCgf_dt')
#        plt.axhline(y=0, color='r', linestyle='--')
#        plt.xlabel("time, s")
#        plt.ylabel("dCgb/dt, (1/m³/s)")
#        plt.title("dCgb/dt vs time")
#        plt.legend()
#        plt.grid(True)
#        plt.savefig(f"{save_dir}/dCg_dt_vs_time.png")
#        plt.close()
    def plot_debug_history(self, save_dir: str = 'debug_plots/'):
        """绘制并保存调试历史图表，添加裂变密度作为第二X轴"""
        import os
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.ticker import FuncFormatter, ScalarFormatter
        from matplotlib.font_manager import FontProperties
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        t = np.array(self.debug_history['time'])
        
        # 计算裂变密度 (fissions/m³)
        fission_rate = self.params.get('fission_rate', 5e19)  # 默认值5e19 fissions/m³/s
        fission_density = t * fission_rate
        
        # 创建裂变密度格式化函数
        def fission_formatter(x, pos):
            if x >= 1e27:
                return f"{x/1e27:.1f}×10²⁷"
            elif x >= 1e24:
                return f"{x/1e24:.1f}×10²⁴"
            elif x >= 1e21:
                return f"{x/1e21:.1f}×10²¹"
            else:
                return f"{x:.1e}"
        
        # 设置中文字体支持（如果需要）
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']  # 使用黑体或Arial Unicode MS
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        except:
            pass
        
        # 创建双轴绘图函数（支持多条曲线）
        def plot_multiple_with_dual_x(x_data, y_data_list, labels, colors, styles, 
                                     x_label, y_label, title, filename):
            fig, ax1 = plt.subplots(figsize=(12, 7))
            
            # 绘制多条数据线
            for i, y_data in enumerate(y_data_list):
                ax1.plot(x_data, y_data, color=colors[i], linestyle=styles[i], 
                        linewidth=1.8, label=labels[i])
            
            ax1.set_xlabel(x_label, fontsize=12)
            ax1.set_ylabel(y_label, fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.tick_params(axis='y')
            
            # 创建第二X轴（裂变密度）
            ax2 = ax1.twiny()
            ax2.set_xlim(ax1.get_xlim())  # 共享相同X范围
            ax2.set_xlabel('裂变密度 (fissions/m³)', fontsize=12, labelpad=12)
            
            # 设置裂变密度刻度
#            ax2.xaxis.set_major_formatter(FuncFormatter(fission_formatter))
            
            # 添加网格
            ax2.grid(True, linestyle=':', alpha=0.4)
            
            # 添加图例
            ax1.legend(loc='best', fontsize=10, framealpha=0.9)
            
            plt.title(title, fontsize=14, pad=15)
            plt.savefig(f"{save_dir}/{filename}", dpi=150, bbox_inches='tight')
            plt.close()
        
        # 创建双轴散点绘图函数（支持多条曲线）
        def scatter_multiple_with_dual_x(x_data, y_data_list, labels, colors, markers, 
                                        x_label, y_label, title, filename):
            fig, ax1 = plt.subplots(figsize=(12, 7))
            
            # 绘制多条散点图
            for i, y_data in enumerate(y_data_list):
                ax1.scatter(x_data, y_data, s=25, color=colors[i], 
                           marker=markers[i], alpha=0.8, label=labels[i])
            
            ax1.set_xlabel(x_label, fontsize=12)
            ax1.set_ylabel(y_label, fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.tick_params(axis='y')
            
            # 创建第二X轴（裂变密度）
            ax2 = ax1.twiny()
            ax2.set_xlim(ax1.get_xlim())  # 共享相同X范围
            ax2.set_xlabel('裂变密度 (fissions/m³)', fontsize=12, labelpad=12)
            
            # 设置裂变密度刻度
#            ax2.xaxis.set_major_formatter(FuncFormatter(fission_formatter))
            
            # 添加网格
            ax2.grid(True, linestyle=':', alpha=0.4)
            
            # 添加图例
            ax1.legend(loc='best', fontsize=10, framealpha=0.9)
            
            plt.title(title, fontsize=14, pad=15)
            plt.savefig(f"{save_dir}/{filename}", dpi=150, bbox_inches='tight')
            plt.close()
        
        # 1. 绘制半径随时间的变化 (Rcb 和 Rcf)
        plot_multiple_with_dual_x(
            t, 
            [self.debug_history['Rcb'], self.debug_history['Rcf']],
            labels=['基体气泡半径 (Rcb)', '界面气泡半径 (Rcf)'],
            colors=['blue', 'red'],
            styles=['-', '--'],
            x_label="时间 (秒)", 
            y_label="半径 (米)", 
            title="气泡半径 vs 时间", 
            filename="radius_comparison.png"
        )
        
        # 2. 绘制压力随时间的变化 (Pg_b 和 Pg_f)
        plot_multiple_with_dual_x(
            t, 
            [self.debug_history['Pg_b'], ],#self.debug_history['Pg_f']],
            labels=['基体气泡压力 (Pg_b)', ],#'界面气泡压力 (Pg_f)'],
            colors=['green', ],#'purple'],
            styles=['-',],# '--'],
            x_label="时间 (秒)", 
            y_label="压力 (Pa)", 
            title="气泡内压 vs 时间", 
            filename="pressure_comparison.png"
        )
        
        # 3. 绘制过压随时间的变化 (Pext_b 和 Pext_f)
        plot_multiple_with_dual_x(
            t, 
            [self.debug_history['Pext_b'], self.debug_history['Pext_f']],
            labels=['基体气泡过压 (Pext_b)', '界面气泡过压 (Pext_f)'],
            colors=['darkorange', 'brown'],
            styles=['-', '--'],
            x_label="时间 (秒)", 
            y_label="过压 (Pa)", 
            title="气泡过压 vs 时间", 
            filename="excess_pressure_comparison.png"
        )
        
        # 4. 绘制热平衡空位浓度随时间的变化 (cv_star_b 和 cv_star_f)
        plot_multiple_with_dual_x(
            t, 
            [self.debug_history['cv_star_b'], self.debug_history['cv_star_f']],
            labels=['基体热平衡空位浓度 (cv_star_b)', '界面热平衡空位浓度 (cv_star_f)'],
            colors=['teal', 'magenta'],
            styles=['-', '--'],
            x_label="时间 (秒)", 
            y_label="空位浓度 (cm⁻³)", 
            title="热平衡空位浓度 vs 时间", 
            filename="cv_star_comparison.png"
        )
        
        # 5. 绘制半径变化率随时间的变化 (dRcb_dt 和 dRcf_dt)
        plot_multiple_with_dual_x(
            t, 
            [self.debug_history['dRcb_dt'], self.debug_history['dRcf_dt']],
            labels=['基体气泡半径变化率 (dRcb_dt)', '界面气泡半径变化率 (dRcf_dt)'],
            colors=['navy', 'darkred'],
            styles=['-', '--'],
            x_label="时间 (秒)", 
            y_label="半径变化率 (m/s)", 
            title="气泡半径变化率 vs 时间", 
            filename="dR_dt_comparison.png"
        )
        
        # 6. 绘制气体浓度变化率随时间的变化 (dCgb_dt 和 dCgf_dt)
        plot_multiple_with_dual_x(
            t, 
            [self.debug_history['dCgb_dt'], self.debug_history['dCgf_dt']],
            labels=['基体气体浓度变化率 (dCgb_dt)', '界面气体浓度变化率 (dCgf_dt)'],
            colors=['darkcyan', 'darkviolet'],
            styles=['-', '--'],
            x_label="时间 (秒)", 
            y_label="浓度变化率 (1/m³/s)", 
            title="气体浓度变化率 vs 时间", 
            filename="dCg_dt_comparison.png"
        )

if __name__ == '__main__':
    params = create_default_parameters()
    model = GasSwellingModel(params)
    print("Initial State :", model.initial_state)
    try:
        derivatives_t0 = model._equations(0, model.initial_state)
        print("Derivatives at t=0:", derivatives_t0)
    except Exception as e:
        print(f"Error evaluating equations at t=0: {e}")

    try:
        result = model.solve(t_span=(0, 3600*10), t_eval=np.linspace(0, 3600*10, 101))
        print("\nSimulation successful.")
        print("Result keys:", list(result.keys()))
        # Calculate final radii for info
        final_Rcb = result['Rcb'][-1]
        final_Rcf = result['Rcf'][-1]
        print(f"Final Rcb: {final_Rcb*1e9:.2f} nm")
        print(f"Final Rcf: {final_Rcf*1e9:.2f} nm")
        final_swelling = (4/3)*np.pi*(final_Rcb**3 * result['Ccb'][-1] + final_Rcf**3 * result['Ccf'][-1])*100
        print(f"Final Swelling: {final_swelling:.4f} %")
    except Exception as e:
        print(f"\nError during simulation: {e}")



import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Tuple, List, Optional
from ..params.parameters import create_default_parameters
import logging
import warnings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='euler_model.log',
    filemode='w'
)
logger = logging.getLogger('euler_model')

class EulerGasSwellingModel:
    """气体肿胀模型Euler简化版本,使用显式Euler方法替代solve_ivp"""

    def __init__(self, params: Optional[Dict] = None):
        """初始化模型参数"""
        self.params = params if params else create_default_parameters()
        self.params.setdefault('Zvc', 1.0)  # Cavity bias for vacancy
        self.params.setdefault('Zic', 1.0)  # Cavity bias for interstitial
        
        # 设置新增优化参数的默认值（如果未提供）
        self.params.setdefault('critical_radius', 2e-9)  # 默认临界半径2nm
        self.params.setdefault('radius_smoothing_factor', 0.8)  # 半径演化平滑因子
        self.params.setdefault('pressure_scaling_factor', 0.5)  # 小气泡内压力缩放因子
        self.params.setdefault('vacancy_contribution_weight', 1.2)  # 空位贡献项权重
        
        self.initial_state = self._initialize_state()
        self.solver_success = True  # 初始化求解器状态标志
        self.num_warnings = 0  # 记录警告信息数量
        self.warning_count = 0  # 新增：记录警告计数
        self.max_warnings = 100  # 最大警告信息数量,防止日志过大
        self.step_count = 0  # 记录计算步数
        
        # 添加额外的调试变量 - 记录关键变量的历史
        self.debug_history = {
            'time': [],
            'Rcb': [],
            'Rcf': [],
            'Pg_b': [],
            'Pg_f': [],
            'Pext_b': [],
            'Pext_f': [],
            'cv_star_b': [],
            'cv_star_f': [],
            'dRcb_dt': [],
            'dRcf_dt': [],
            'dCgb_dt': [],
            'dCgf_dt': [],
            'surf_tension_b': [],  # 记录表面张力
            'surf_tension_f': [],
            'radius_factor_b': [],  # 记录半径平滑因子
            'radius_factor_f': []
        }
        
    def _calculate_cv0(self) -> float:
        """计算无缺陷时的热平衡空位浓度(公式16)"""
        T = self.params['temperature']
        C = self.params['Evf_coeffs']
        Evf = C[0] + C[1]*T
        
        # 指数参数，限制以防止溢出
        exponent_arg = -Evf / (self.params['kB_ev'] * T)
        if exponent_arg < -700:
            logger.warning(f"cv0计算中指数参数过小: {exponent_arg}, 已限制为-700")
            exponent_arg = -700
        elif exponent_arg > 700:
            logger.warning(f"cv0计算中指数参数过大: {exponent_arg}, 已限制为700")
            exponent_arg = 700
            
        cv0 = np.exp(exponent_arg)
        logger.debug(f"计算的cv0值: {cv0}, 指数参数: {exponent_arg}")
        return cv0

    def _calculate_ci0(self) -> float:
        """计算无缺陷时的热平衡间隙原子浓度"""
        T = self.params['temperature']
        C = self.params['Eif_coeffs']
        Eif = C[0] + C[1]*T + C[2]*T**2 + C[3]*T**3
        
        # 指数参数，限制以防止溢出
        exponent_arg = -Eif / (self.params['kB_ev'] * T)
        if exponent_arg < -700:
            logger.warning(f"ci0计算中指数参数过小: {exponent_arg}, 已限制为-700")
            exponent_arg = -700
        elif exponent_arg > 700:
            logger.warning(f"ci0计算中指数参数过大: {exponent_arg}, 已限制为700")
            exponent_arg = 700
            
        ci0 = np.exp(exponent_arg)
        logger.debug(f"计算的ci0值: {ci0}, 指数参数: {exponent_arg}")
        return ci0

    def _gas_influx(self, Cgb: float, Cgf: float) -> float:
        """计算从基体扩散到相界面的气体原子通量(公式2)"""
        return (12.0 /( self.params['grain_diameter'])**2) * self.params['Dgb'] * (Cgb-Cgf)

    def _calculate_gas_release_rate(self, Cgf: float, Ccf: float, Rcf: float, Ncf: float) -> float:
        """计算气体释放率(公式9-12)"""
        # 几何因子
        theta = 50/180 * np.pi
        ff_theta = 1 - 1.5 * np.cos(theta) + 0.5 * np.cos(theta)**3
        
        # 检查Rcf的有效值
        if Rcf <= 1e-12:
            logger.warning(f"计算气体释放率时Rcf过小: {Rcf}")
            return 0.0
            
        Af = np.pi * Rcf**2 * Ccf * ff_theta  # Eq.10
        Sv_aa = 6.0 / self.params['grain_diameter']  # grain-face area per unit volume, m-1
        Af_max = 0.907 * Sv_aa  # Eq.11
        
        Af_ratio = Af / Af_max
        
        # 计算腔室互连系数 (Eq.12)
        if Af_ratio <= 0.25:
            chi = 0.0
        elif Af_ratio >= 1.0:
            chi = 1.0 
        else:
            chi = Af_ratio
        
        # 重构计算公式增强数值稳定性
        h0 = chi * (Cgf + Ccf * Ncf)
        return 0

    def _calculate_idealgas_pressure(self, Rc: float, Nc: float) -> float:
        """
        使用理想气体状态方程计算气体压力，对小气泡进行特殊处理
        
        改进:
        1. 对小于临界半径的气泡应用压力缩放因子，降低表面张力的影响
        2. 引入压力下限，确保气体压力不会过低
        3. 引入平滑过渡函数，避免压力突变
        """
        # 检查Rc和Nc的有效值，防止除零或负值
        if Rc <= 1e-12:
            logger.warning(f"计算气体压力时Rc过小: {Rc}")
            return 0.0
        if Nc <= 0:
            logger.warning(f"计算气体压力时Nc无效: {Nc}")
            return 0.0
            
        T = self.params['temperature']
        kB = self.params['kB']
        hs=0.6
        bv=8.5e-29        
        # 使用更安全的计算方式，增加数值稳定性
        pressure = Nc * kB * T / (4.0/3.0 * np.pi * Rc**3-Nc* hs* bv)
        
        # 获取临界半径，用于小气泡特殊处理
#        critical_radius = self.params['critical_radius']
#        pressure_scaling_factor = self.params['pressure_scaling_factor']
        
        # 计算压力缩放因子 - 平滑过渡函数
        # 对于小于临界半径的气泡，提高其内部压力以克服表面张力
#        if Rc < critical_radius:
#            # 计算平滑的压力增强因子，随着半径减小而增大
#            radius_ratio = Rc / critical_radius
#            # 使用平滑的S形函数，当半径接近0时，缩放因子接近最大值(1/pressure_scaling_factor)
#            pressure_enhancement = 1.0 + (1.0/pressure_scaling_factor - 1.0) * (1.0 - radius_ratio)**2
#            enhanced_pressure = base_pressure * pressure_enhancement
#            
#            # 记录增强的压力和原始压力
#            if self.num_warnings < self.max_warnings and pressure_enhancement > 1.5:
#                logger.info(f"小气泡压力增强: 原始压力={base_pressure:.4e}Pa, 增强系数={pressure_enhancement:.4f}, 增强后压力={enhanced_pressure:.4e}Pa")
#                self.num_warnings += 1
#                
#            pressure = enhanced_pressure
#        else:
#            pressure = base_pressure
#        
#        # 计算气泡表面张力
#        gamma = self.params['surface_energy']
#        surface_tension = 2 * gamma / Rc
#        
#        # 确保气体压力至少大于表面张力的一定比例，防止气泡收缩
#        min_pressure = surface_tension * 1.05  # 气压至少比表面张力高5%
#        if pressure < min_pressure:
#            if self.num_warnings < self.max_warnings:
#                logger.info(f"气体压力低于表面张力门槛: {pressure:.4e} Pa < {min_pressure:.4e} Pa，已提高至{min_pressure:.4e} Pa")
#                self.num_warnings += 1
#         = base_pressure
                
        # 限制最大压力值，防止计算不稳定
        max_pressure = 1e10  # 设置最大压力上限为100亿Pa
        if pressure > max_pressure:
            if self.num_warnings < self.max_warnings:
                logger.warning(f"计算的气体压力超过上限: {pressure:.4e} Pa，已限制为 {max_pressure:.4e} Pa")
                self.num_warnings += 1
            pressure = max_pressure
                
        return pressure  # 返回计算的压力值
    
    def _calculate_VirialEOSgas_pressure(self, Rc: float, Nc: float) -> float:
        """使用_VirialEOS气体状态方程计算气体压力"""
        if Rc <= 1e-12 or Nc <= 0: return 0.0
        R = self.params['R']
        T = self.params['temperature']
        nu = 4/3 * np.pi * 1e6 * Rc**3 / Nc * 6.02214076e23 #Rc单位换成cm
        b0 = 197.229
        b1 = 120307.145
        b2 = 60.555
        c0 = -22038.723
        c1 = 2292.793
        c2 = -117.564
        d0 = 1030015.045
        d1 = -5.200
        d2 = -280.677
        Bs = b0 + b1/T +b2/T**2
        Cs = c0 + c1/T +c2/T**2
        Ds = d0 + d1/T +d2/T**2

        return R * T * (1.0 + Bs/nu + Cs/nu**2 + Ds/nu**3)/nu   
              
    def _initialize_state(self) -> np.ndarray:
        """初始化状态变量, Ncb, Ncf等"""
        Nc_init = 5.0  # 初始气泡内气体数, atoms
        Cg_init = 0.0  # 初始气体浓度, atoms/m3
        Cc_init = 0.0   # 初始气腔浓度, cavities/m3
        R_init = 1e-8   # 初始半径,进一步增大初始半径以减小气体压力
        cv0 = self._calculate_cv0()  # 初始空位浓度是热平衡浓度
        ci0 = self._calculate_ci0()  # 初始间隙原子浓度是热平衡浓度
        kv_param = self.params['kv_param']
        ki_param = self.params['ki_param']

        # State vector: [Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvb, cib, kvb, kib, cvf, cif, kvf, kif, released_gas]
        return np.array([
            Cg_init,     # 0: Cgb
            Cc_init,     # 1: Ccb
            Nc_init,     # 2: Ncb (Initial atoms per bulk bubble)
            R_init,      # 3: Rcb (Initial radius of bulk bubble)
            Cg_init,     # 4: Cgf
            Cc_init,     # 5: Ccf
            Nc_init,     # 6: Ncf (Initial atoms per boundary bubble)
            R_init,      # 7: Rcf (Initial radius of boundary bubble)
            cv0,         # 8: cvb
            ci0,         # 9: cib
            kv_param,    # 10: kvb
            ki_param,    # 11: kib
            cv0,         # 12: cvf
            ci0,         # 13: cif
            kv_param,    # 14: kvf
            ki_param,    # 15: kif
            0.0          # 16: released_gas
        ])

    def _calculate_derivatives(self, t: float, state: np.ndarray) -> np.ndarray:
        """计算微分方程组右侧导数(公式1-25)
        添加详细的中间计算过程记录，以便诊断数值问题
        """
        # 解包状态向量 (17个变量)
        Cgb, Ccb, Ncb, Rcb, Cgf, Ccf, Ncf, Rcf, cvb, cib, kvb, kib, cvf, cif, kvf, kif, released_gas = state

        # 数值保护：避免半径为零或过大，提高最小半径限制
        min_radius = 1e-10  # 最小半径限制
        max_radius = 1e-4   # 最大半径限制
        
        Rcb_safe = np.clip(Rcb, min_radius, max_radius)
        Rcf_safe = np.clip(Rcf, min_radius, max_radius)
        
        if Rcb != Rcb_safe or Rcf != Rcf_safe:
            if self.num_warnings < self.max_warnings:
                logger.warning(f"半径值超出范围: Rcb={Rcb}, Rcf={Rcf}, 已限制为 [{min_radius}, {max_radius}]")
                self.num_warnings += 1

        # 计算扩散系数
        kB_ev = self.params['kB_ev']
        T = self.params['temperature']
        Dv = self.params['Dv0'] * np.exp(-self.params['Evm'] / (kB_ev * T))
        Di = self.params['Di0'] * np.exp(-self.params['Eim'] / (kB_ev * T))
        
        Dgb = self.params['Dgb_prefactor'] * np.exp(-self.params['Dgb_activation_energy'] / (kB_ev * T)) \
            + self.params['Dgb_fission_term'] * self.params['fission_rate']
            
        Dgf = self.params['Dgf_multiplier'] * Dgb
        
        # 记录计算的扩散系数，用于诊断
        logger.debug(f"计算的扩散系数: Dv={Dv}, Di={Di}, Dgb={Dgb}, Dgf={Dgf}")

        # 点缺陷计算(公式17-24) 
        Zv = self.params['Zv']
        Zi = self.params['Zi']
        rho = self.params['dislocation_density']

        # 位错汇聚强度 (公式 23,24)
        k_vd2 = Zv * rho
        k_id2 = Zi * rho
    
        # 公式21和22,计算基体和界面空腔对点缺陷的汇聚强度
        kvc2_b = 4 * np.pi * Rcb_safe * Ccb * (1 + kvb * Rcb_safe)
        kic2_b = 4 * np.pi * Rcb_safe * Ccb * (1 + kib * Rcb_safe)
        kvc2_f = 4 * np.pi * Rcf_safe * Ccf * (1 + kvf * Rcf_safe)
        kic2_f = 4 * np.pi * Rcf_safe * Ccf * (1 + kif * Rcf_safe)
        
        # 记录汇聚强度值，用于诊断
        logger.info(f"汇聚强度: k_vd2={k_vd2}, k_id2={k_id2}, kvc2_b={kvc2_b}, kic2_b={kic2_b}")

        # Total sink strengths, 公式 19, 20
        kvb2_total = kvc2_b + k_vd2
        kib2_total = kic2_b + k_id2
        kvf2_total = kvc2_f + k_vd2
        kif2_total = kic2_f + k_id2
        
        # Square roots, 避免负数开方
        kvb_new = np.sqrt(np.maximum(kvb2_total, 0.0))
        kib_new = np.sqrt(np.maximum(kib2_total, 0.0))
        kvf_new = np.sqrt(np.maximum(kif2_total, 0.0))
        kif_new = np.sqrt(np.maximum(kif2_total, 0.0))
        
        # 检查汇聚强度是否异常
        if any(v <= 0 for v in [kvb2_total, kib2_total, kvf2_total, kif2_total]):
            if self.num_warnings < self.max_warnings:
                logger.warning(f"汇聚强度出现负值: kvb2={kvb2_total}, kib2={kib2_total}, kvf2={kvf2_total}, kif2={kif2_total}")
                self.num_warnings += 1

        # 基体和晶界处的点缺陷浓度 (dcv/dt, dci/dt - 公式 17, 18)
        # 间隙与空位复合因子
        alpha = 4 * np.pi * self.params['recombination_radius'] * (Dv + Di)/self.params['Omega']
        phi = self.params['displacement_rate'] * self.params['fission_rate']
        
        # 基体空位变化率
        dcvb_dt = phi - kvb2_total * Dv * cvb - alpha * cvb * cib
        
        # 基体间隙原子变化率
        dcib_dt = phi - kib2_total * Di * cib - alpha * cvb * cib
        
        # 晶界空位变化率
        dcvf_dt = phi - kvf2_total * Dv * cvf - alpha * cvf * cif
        
        # 晶界间隙原子变化率
        dcif_dt = phi - kif2_total * Di * cif - alpha * cvf * cif
        
        # 记录点缺陷浓度变化率
        logger.info(f"点缺陷浓度变化率: term1={phi}, term2={kvb2_total * Dv * cvb}, term3={alpha * cvb * cib}")

        # 计算空腔附近的空位浓度 （公式15）
        cv0 = self._calculate_cv0()
        kB_J = self.params['kB']

        # 计算空腔中的气压 $P_g$, 最小值为1Pa
        Pg_b = self._calculate_VirialEOSgas_pressure(Rcb_safe, Ncb)
        Pg_f = self._calculate_VirialEOSgas_pressure(Rcf_safe, Ncf)
        
        gamma = self.params['surface_energy']
        sigma_ext = self.params['hydrastatic_pressure']
        
        # 获取临界半径和平滑因子
        critical_radius = self.params['critical_radius']
        radius_smoothing_factor = self.params['radius_smoothing_factor']
        
        # 计算表面张力，使用临界半径平滑过渡
        # 当半径小于临界半径时，逐渐减弱表面张力的影响
        surface_tension_raw_b = 2 * gamma / Rcb_safe
        surface_tension_raw_f = 2 * gamma / Rcf_safe
        
        # 对于小于临界半径的气泡，计算表面张力减弱因子
        if Rcb_safe < critical_radius:
            radius_ratio_b = Rcb_safe / critical_radius
            # 使用平滑过渡函数，当半径接近最小值时，表面张力影响逐渐减弱
            radius_factor_b = radius_ratio_b**2 * (3 - 2*radius_ratio_b)  # 埃尔米特插值
            # 根据平滑因子调整表面张力
            surface_tension_b = surface_tension_raw_b * (radius_smoothing_factor + (1-radius_smoothing_factor)*radius_factor_b)
        else:
            radius_factor_b = 1.0
            surface_tension_b = surface_tension_raw_b
            
        if Rcf_safe < critical_radius:
            radius_ratio_f = Rcf_safe / critical_radius
            radius_factor_f = radius_ratio_f**2 * (3 - 2*radius_ratio_f)
            surface_tension_f = surface_tension_raw_f * (radius_smoothing_factor + (1-radius_smoothing_factor)*radius_factor_f)
        else:
            radius_factor_f = 1.0
            surface_tension_f = surface_tension_raw_f
            
        # 记录表面张力调整因子
        self.debug_history['surf_tension_b'].append(surface_tension_b)
        self.debug_history['surf_tension_f'].append(surface_tension_f)
        self.debug_history['radius_factor_b'].append(radius_factor_b)
        self.debug_history['radius_factor_f'].append(radius_factor_f)
        
        # 计算有效压力差，确保不会出现极端值
        Pext_b = np.clip(Pg_b - surface_tension_b - sigma_ext, -1e9, 1e9)
        Pext_f = np.clip(Pg_f - surface_tension_f - sigma_ext, -1e9, 1e9)
        
        # 记录计算的压力值，用于诊断
        logger.debug(f"压力计算: Pg_b={Pg_b}, Pg_f={Pg_f}, Pext_b={Pext_b}, Pext_f={Pext_f}")
        logger.debug(f"表面张力: 原始_b={surface_tension_raw_b}, 调整_b={surface_tension_b}, 原始_f={surface_tension_raw_f}, 调整_f={surface_tension_f}")
        
        # 检查压力异常
        if Pext_b > 0:
            logger.info(f"基体空腔为过压状态: Pext_b={Pext_b}")
       # else:
        #    logger.info(f"基体空腔为欠压状态: Pext_b={Pext_b}")
        if Pext_f > 0:
            logger.info(f"界面空腔为过压状态: Pext_f={Pext_f}")
       # else:
        #    logger.info(f"界面空腔为欠压状态: Pext_f={Pext_f}")
        
        # 指数项
        arg_b = - Pext_b * self.params['Omega'] / (kB_J * T)
        arg_f = - Pext_f * self.params['Omega'] / (kB_J * T)
        
        # 检查指数参数是否超出范围
        if abs(arg_b) > 700 or abs(arg_f) > 700:
            if self.num_warnings < self.max_warnings:
                logger.warning(f"指数参数超出范围: arg_b={arg_b}, arg_f={arg_f}")
                self.num_warnings += 1
        
        # 限制指数参数范围，防止数值溢出
#        arg_b = np.clip(arg_b, -700, 700)
#        arg_f = np.clip(arg_f, -700, 700)
        
        # 分别计算基体和界面的空腔附近空位浓度$c_v^*$
        cv_star_b = cv0 * np.exp(arg_b)
        cv_star_f = cv0 * np.exp(arg_f)
        
        # 记录空位浓度计算过程
        logger.debug(f"空位浓度: cv0={cv0}, cv_star_b={cv_star_b}, cv_star_f={cv_star_f}")
        logger.debug(f"指数参数: arg_b={arg_b}, arg_f={arg_f}")

        # 公式14 - 计算空腔半径变化率
        # 检查分母是否接近零
        denom_b = 4*np.pi*Rcb_safe**2*Ccb
        denom_f = 4*np.pi*Rcf_safe**2*Ccf
        
        if denom_b < 1e-20 or denom_f < 1e-20:
            if self.num_warnings < self.max_warnings:
                logger.warning(f"空腔半径计算分母接近零: denom_b={denom_b}, denom_f={denom_f}")
                self.num_warnings += 1
                
        # 防止除零
        denom_b = max(denom_b, 1e-20)
        denom_f = max(denom_f, 1e-20)
            
        # 分别计算基体和界面空腔半径变化率项
        # 空位被空腔吸收
        dRcb_term1 = kvc2_b*Dv*cvb
        # 间隙原子被空腔吸收
        dRcb_term2 = kic2_b*Di*cib
        # 空位发射
        dRcb_term3 = kvc2_b*Dv*cv_star_b
        
        # 同样计算界面空腔项
        dRcf_term1 = kvc2_f*Dv*cvf
        dRcf_term2 = kic2_f*Di*cif
        dRcf_term3 = kvc2_f*Dv*cv_star_f
        
        # 计算半径变化率
        dRcb_dt = (dRcb_term1 - dRcb_term2 - dRcb_term3) / denom_b
        dRcf_dt = (dRcf_term1 - dRcf_term2 - dRcf_term3) / denom_f
        
        # 记录半径变化率计算过程
        logger.info(f"半径变化率计算: dRcb_term1={dRcb_term1}, dRcb_term2={dRcb_term2}, dRcb_term3={dRcb_term3}")
        logger.debug(f"半径变化率: dRcb_dt={dRcb_dt}, dRcf_dt={dRcf_dt}")

        # 从基体扩散到相界面的气体通量
        g0 = self._gas_influx(Cgb, Cgf)
        # 气体释放率，简化为0，以便诊断其他问题
        h0 = self._calculate_gas_release_rate(Cgf, Ccf, Rcf_safe, Ncf)
        
        # 公式13 - 计算每个界面空腔内气体原子数变化率
        dNcf_dt = 4 * np.pi * Rcf_safe * Dgf * Cgf - h0 * Ncf

        # 基体中气体原子浓度变化速率 (dCgb/dt - 公式 1)
        # 气泡形核吸收项
        term1_Cgb = -16 * np.pi * self.params['Fnb'] * self.params['Xe_radii'] * Dgb * Cgb**2
        # 气体原子扩散吸收项
        term2_Cgb = -4 * np.pi * Rcb_safe * Dgb * Cgb * Ccb
        # 气体原子迁移到晶界
        term3_Cgb = -g0
        # 裂变产生的气体原子
        term4_Cgb = self.params['gas_production_rate'] * self.params['fission_rate']
        # 气泡气体原子重溶
        term5_Cgb = self.params['resolution_rate'] * Ccb * Ncb
        dCgb_dt = term1_Cgb + term2_Cgb + term3_Cgb + term4_Cgb + term5_Cgb
        
        # 记录气体浓度变化率计算过程
        logger.debug(f"气体浓度变化率计算: term1_Cgb={term1_Cgb}, term2_Cgb={term2_Cgb}, term3_Cgb={term3_Cgb}")
        logger.debug(f"气体浓度变化率: dCgb_dt={dCgb_dt}")

        # 基体气泡浓度变化速率 (dCcb/dt - 公式 3)
        Ncb_safe_denom = max(Ncb, 2)
        dCcb_dt = (16 * np.pi * self.params['Fnb'] * self.params['Xe_radii'] * Dgb * Cgb**2) / Ncb_safe_denom

        # 每个空腔内气体原子数变化速率 (dNcb/dt - 公式 5)
        # 从基体扩散到空腔的气体原子速率
        term1_Ncb = 4 * np.pi * Rcb_safe * Dgb * Cgb
        dNcb_dt = term1_Ncb - self.params['resolution_rate'] * Ncb

        # 晶界气体浓度变化率 (dCgf/dt - 公式 6)
        # 气体原子形核吸收项
        term1_Cgf = -16 * np.pi * self.params['Fnf'] * self.params['Xe_radii'] * Dgf * Cgf**2
        # 气体原子扩散吸收项
        term2_Cgf = -4 * np.pi * Rcf_safe * Dgf * Cgf * Ccf
        # 从基体迁移到晶界的气体原子
        term3_Cgf = g0
        # 气体原子在晶界释放
        term4_Cgf = h0 * Cgf
        # 公式 6
        dCgf_dt = term1_Cgf + term2_Cgf + term3_Cgf - term4_Cgf

        # 晶界空腔浓度变化率 (dCcf/dt - 公式 7)
        Ncf_safe_denom = max(Ncf, 2)
        dCcf_dt = (16 * np.pi * self.params['Fnf'] * self.params['Xe_radii'] * Dgf * Cgf**2) / Ncf_safe_denom

        # 累积气体释放率 (dh_dt)
        dh_dt = h0

        # 修正导数数组维度并增强数值稳定性 (17个元素)
#        derivatives = np.array([
#            np.clip(dCgb_dt, -1e23, 1e25),    # 0: Cgb
#            np.clip(dCcb_dt, -1e23, 1e23),    # 1: Ccb
#            np.clip(dNcb_dt, -1e8, 1e8),      # 2: Ncb
#            np.clip(dRcb_dt, -1e5, 1e5),      # 3: Rcb
#            np.clip(dCgf_dt, -1e20, 5e25),    # 4: Cgf
#            np.clip(dCcf_dt, -1e20, 5e20),    # 5: Ccf
#            np.clip(dNcf_dt, -1e8, 1e8),      # 6: Ncf
#            np.clip(dRcf_dt, -1e5, 1e5),      # 7: Rcf
#            np.clip(dcvb_dt, -1e8, 5e20),     # 8: cvb
#            np.clip(dcib_dt, -1e8, 5e20),     # 9: cib
#            np.clip(kvb_new - kvb, -1e10, 1e10),  # 10: kvb导数
#            np.clip(kib_new - kib, -1e10, 1e10),  # 11: kib导数
#            np.clip(dcvf_dt, -1e8, 1e8),      # 12: cvf
#            np.clip(dcif_dt, -1e8, 1e8),      # 13: cif
#            np.clip(kvf_new - kvf, -1e10, 1e10),  # 14: kvf导数
#            np.clip(kif_new - kif, -1e10, 1e10),  # 15: kif导数
#            np.clip(dh_dt, -1e5, 1e5),        # 16: released_gas
#        ])
        derivatives = np.array([
            dCgb_dt,    # 0: Cgb
            dCcb_dt,    # 1: Ccb
            dNcb_dt,      # 2: Ncb
            dRcb_dt,      # 3: Rcb
            dCgf_dt,    # 4: Cgf
            dCcf_dt,    # 5: Ccf
            dNcf_dt,      # 6: Ncf
            dRcf_dt,      # 7: Rcf
            dcvb_dt,     # 8: cvb
            dcib_dt,     # 9: cib
            kvb_new - kvb,  # 10: kvb导数
            kib_new - kib,  # 11: kib导数
            dcvf_dt,      # 12: cvf
            dcif_dt,      # 13: cif
            kvf_new - kvf,  # 14: kvf导数
            kif_new - kif,  # 15: kif导数
            dh_dt,        # 16: released_gas
        ])
        # 检查导数是否包含NaN或Inf值
        if not np.all(np.isfinite(derivatives)):
            nan_indices = np.where(~np.isfinite(derivatives))[0]
            if self.num_warnings < self.max_warnings:
                logger.warning(f"导数包含NaN或Inf值: 索引={nan_indices}")
                self.num_warnings += 1
            # 替换NaN和Inf值
            derivatives = np.nan_to_num(derivatives, nan=0.0, posinf=1e10, neginf=-1e10)
            
        # 更新调试历史记录
        self.debug_history['time'].append(t)
        self.debug_history['Rcb'].append(Rcb_safe)
        self.debug_history['Rcf'].append(Rcf_safe)
        self.debug_history['Pg_b'].append(Pg_b)
        self.debug_history['Pg_f'].append(Pg_f)
        self.debug_history['Pext_b'].append(Pext_b)
        self.debug_history['Pext_f'].append(Pext_f)
        self.debug_history['cv_star_b'].append(cv_star_b)
        self.debug_history['cv_star_f'].append(cv_star_f)
        self.debug_history['dRcb_dt'].append(dRcb_dt)
        self.debug_history['dRcf_dt'].append(dRcf_dt)
        self.debug_history['dCgb_dt'].append(dCgb_dt)
        self.debug_history['dCgf_dt'].append(dCgf_dt)
            
        return derivatives
    def euler_solve(self, t_span: Tuple[float, float] = (0, 3600),
                  t_eval: Optional[np.ndarray] = None, dt: float = 0.1, max_dt: float = 0.5, max_steps: int = 1000,
                  output_interval: int = 100) -> Dict:
        """使用Euler方法求解微分方程组
        
        参数:
            t_span: 时间范围，包含开始和结束时间
            t_eval: 需要计算的时间点
            dt: 初始时间步长，如果为None，则使用参数中指定的时间步长或自动计算
            max_dt: 最大时间步长，如果为None，则使用参数中指定的最大时间步长
            max_steps: 最大计算步数，如果为None则不限制步数
            output_interval: 状态输出的步数间隔，默认每100步输出一次
        
        返回:
            包含计算结果的字典
        """
        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 100)
        
        # 获取初始时间步长
        if dt is None:
            # 尝试从参数中获取时间步长
            if 'time_step' in self.params:
                dt = self.params['time_step']
            elif len(t_eval) > 1:
                # 使用t_eval中的最小间隔作为建议步长
                dt_suggested = np.min(np.diff(t_eval))
                # 选择更小的步长以确保稳定性
                dt = min(dt_suggested / 10, 0.1)
            else:
                dt = 1e-9  # 非常小的默认初始时间步长以确保稳定性
        
        # 获取最大时间步长
        if max_dt is None:
            if 'max_time_step' in self.params:
                max_dt = self.params['max_time_step']
            else:
                max_dt = 0.01  # 默认最大时间步长
                
        logger.info(f"使用Euler方法求解，初始时间步长: {dt}秒，最大时间步长: {max_dt}秒")
        if max_steps is not None:
            logger.info(f"最大计算步数限制: {max_steps}步")
        logger.info(f"状态输出间隔: 每{output_interval}步输出一次")
        
        # 初始状态
        state = np.clip(self.initial_state, 1e-10, 1e20)  # 限制初始值范围，提高最小值
        t_current = t_span[0]
        t_end = t_span[1]
        
        # 用于存储结果的列表
        t_points = [t_current]
        state_history = [state.copy()]
        
        # 计算实际步数
        if dt <= 0:
            raise ValueError("dt must be positive")
        n_steps = int((t_end - t_current) / dt) + 1
        
        # 记录求解开始
        logger.info(f"开始Euler求解: 从t={t_current}到t={t_end}，步数={n_steps}")
        
        try:
            # 使用Euler方法逐步计算
            warning_count = 0
            max_warnings = 10  # 限制警告数量以避免日志过大
            
            # 主循环 - 逐步推进时间
            self.step_count = 0
            while t_current < t_end:
                # 检查是否达到最大步数限制
                if max_steps is not None and self.step_count >= max_steps:
                    logger.info(f"已达到最大步数限制: {max_steps}步，在t={t_current}秒处停止计算")
                    break
                
                # 自适应时间步长 - 确保不会超过t_end
                if t_current + dt > t_end:
                    dt = t_end - t_current
                
                # 确保时间步长不超过最大值
                dt = min(dt, max_dt)
                
                # 计算导数
                derivatives = self._calculate_derivatives(t_current, state)
                
                # 检查导数是否有效
                if not np.all(np.isfinite(derivatives)):
                    if warning_count < max_warnings:
                        logger.warning(f"t={t_current}: 导数包含无效值，已替换为0")
                        warning_count += 1
                    derivatives = np.nan_to_num(derivatives, nan=0.0, posinf=0.0, neginf=0.0)
                
                # 使用Euler方法更新状态
                new_state = state + dt * derivatives
                
                # 检查新状态是否合理
                if not np.all(np.isfinite(new_state)):
                    if warning_count < max_warnings:
                        logger.warning(f"t={t_current}: 新状态包含无效值，尝试限制导数幅度")
                        warning_count += 1
                    # 尝试减小时间步长以避免不稳定
                    dt = dt / 2
                    logger.info(f"减小时间步长至 {dt}秒")
                    continue
                
                # 对半径进行有效性检查
                if new_state[3] < 5e-10 or new_state[7] < 5e-10:
                    if warning_count < max_warnings:
                        warnings.warn(
                            f"t={t_current}: 气泡半径过小，可能导致数值不稳定",
                            UserWarning
                        )
                        warning_count += 1
                        self.warning_count += 1
                
                # 应用限制以增强稳定性，提高最小值限制
                new_state = np.clip(new_state, 1e-10, 1e28)
                
                # 特别保护气泡半径（索引3和7），确保它们不会太小
                new_state[3] = np.clip(new_state[3], 1e-10, 1e-5)  # 增大最小半径限制
                new_state[7] = np.clip(new_state[7], 1e-10, 1e-5)  # 增大最小半径限制
                
                # 更新状态和时间
                state = new_state
                t_current += dt
                
                # 存储计算点
                t_points.append(t_current)
                state_history.append(state.copy())
                
                # 增加步数计数
                self.step_count += 1
                
                # 每隔output_interval步输出当前状态，增强日志记录
                if self.step_count % output_interval == 0:
                    # 计算气泡内压力
                    Pg_b = self._calculate_VirialEOSgas_pressure(state[3], state[2])
                    Pg_f = self._calculate_VirialEOSgas_pressure(state[7], state[6])
                    
                    # 计算气体分配情况
                    gas_in_bulk = state[0]
                    gas_in_bulk_bubbles = state[1] * state[2]
                    gas_in_interface = state[4]
                    gas_in_interface_bubbles = state[5] * state[6]
                    gas_released = state[16]
                    total_gas = gas_in_bulk + gas_in_bulk_bubbles + gas_in_interface + gas_in_interface_bubbles + gas_released
                    
                    # 增强的状态日志
                    logger.info(f"当前状态 (步数={self.step_count}): t={t_current:.6f}s")
                    logger.info(f"- 半径: Rcb={state[3]*1e9:.4f}nm, Rcf={state[7]*1e9:.4f}nm")
                    logger.info(f"- 气泡内气体原子数: Ncb={state[2]:.4f}, Ncf={state[6]:.4f}")
                    logger.info(f"- 气泡内压: Pg_b={Pg_b:.4e}Pa, Pg_f={Pg_f:.4e}Pa")
                    logger.info(f"- 气体分配: 基体={gas_in_bulk/total_gas*100:.2f}%, 基体气泡={gas_in_bulk_bubbles/total_gas*100:.2f}%, 界面={gas_in_interface/total_gas*100:.2f}%, 界面气泡={gas_in_interface_bubbles/total_gas*100:.2f}%, 释放={gas_released/total_gas*100:.2f}%")
                    
                # 尝试增加时间步长（如果前面的计算稳定），加速时间步长增长
                if self.step_count % 5 == 0 and dt < max_dt:
                    dt = min(dt * 1.2, max_dt)  # 更快速增加时间步长，但不超过最大步长
                
                # 定期记录进度
                if self.step_count % 1000 == 0:
                    # 计算完成百分比
                    percent_complete = (t_current / t_end) * 100
                    logger.info(f"计算进度: {percent_complete:.2f}% (t={t_current:.6f}/{t_end:.2f}), 步数={self.step_count}, 当前时间步长={dt:.6f}s")
            
            # 根据t_eval插值获取所需时间点的状态
            # 将结果转换为numpy数组便于处理
            t_array = np.array(t_points)
            states_array = np.array(state_history)
            
            # 对每个请求的时间点进行插值
            result_states = np.zeros((len(t_eval), len(self.initial_state)))
            for i in range(len(self.initial_state)):
                # 线性插值获取每个状态变量在t_eval时间点的值
                result_states[:, i] = np.interp(t_eval, t_array, states_array[:, i])
            
            self.solver_success = True
            logger.info(f"Euler求解成功完成，共{self.step_count}步")
            
        except Exception as e:
            logger.error(f"Euler求解失败: {str(e)}")
            self.solver_success = False
            # 如果失败，返回已计算的部分结果
            t_eval = np.array(t_points)
            result_states = np.array(state_history)
        
        # 将结果映射到字典
        results_dict = {
            'time': t_eval,
            'Cgb': result_states[:, 0],
            'Ccb': result_states[:, 1],
            'Ncb': result_states[:, 2],
            'Rcb': result_states[:, 3],
            'Cgf': result_states[:, 4],
            'Ccf': result_states[:, 5],
            'Ncf': result_states[:, 6],
            'Rcf': result_states[:, 7],
            'cvb': result_states[:, 8],
            'cib': result_states[:, 9],
            'kvb': result_states[:, 10],
            'kib': result_states[:, 11],
            'cvf': result_states[:, 12],
            'cif': result_states[:, 13],
            'kvf': result_states[:, 14],
            'kif': result_states[:, 15],
            'released_gas': result_states[:, 16]
        }
        
        return results_dict
    
    def solve(self, t_span: Tuple[float, float] = (0, 3600),
              t_eval: Optional[np.ndarray] = None, dt: float = 0.1) -> Dict:
        """求解微分方程组（Euler方法实现）
        
        这是与原始模型兼容的接口
        """
        return self.euler_solve(t_span, t_eval, dt)
    
    def plot_debug_history(self, save_dir="euler_debug_plots"):
        """绘制调试历史数据，显示关键变量随时间的变化"""
        import os
        
        # 创建保存目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 检查是否有历史数据
        if not self.debug_history['time']:
            logger.warning("没有调试历史数据可绘制")
            return
            
        t = np.array(self.debug_history['time'])
        
        # 绘制半径随时间的变化
        plt.figure(figsize=(10, 6))
        plt.plot(t, self.debug_history['Rcb'], label='Rcb')
        plt.plot(t, self.debug_history['Rcf'], label='Rcf')
        plt.xlabel("time, s")
        plt.ylabel("radius,m")
        plt.title("RADIUS VS TIME")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{save_dir}/radius_vs_time.png")
        plt.close()
        
        # 绘制压力随时间的变化
        plt.figure(figsize=(10, 6))
        plt.plot(t, self.debug_history['Pg_b'], label='Pg_b')
        plt.plot(t, self.debug_history['Pg_f'], label='Pg_f')
        plt.xlabel("time, s")
        plt.ylabel("Pressure, Pa")
        plt.title("PRESSURE VS TIME")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{save_dir}/pressure_vs_time.png")
        plt.close()
        
        # 绘制过压随时间的变化
        plt.figure(figsize=(10, 6))
        plt.plot(t, self.debug_history['Pext_b'], label='Pext_b')
        plt.plot(t, self.debug_history['Pext_f'], label='Pext_f')
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel("time, s")
        plt.ylabel("Pressure bias, Pa")
        plt.title("PRESSURE BIAS VS TIME")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{save_dir}/excess_pressure_vs_time.png")
        plt.close()
        
        # 绘制热平衡空位浓度随时间的变化
        plt.figure(figsize=(10, 6))
        plt.plot(t, self.debug_history['cv_star_b'], label='cv_star_b')
        plt.plot(t, self.debug_history['cv_star_f'], label='cv_star_f')
        plt.xlabel("time, s")
        plt.ylabel("VOID CONCERNTRATION,CM-3")
        plt.title("VOID CONCERNTRATION VS TIME")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{save_dir}/cv_star_vs_time.png")
        plt.close()
        
        # 绘制半径变化率随时间的变化
        plt.figure(figsize=(10, 6))
        plt.plot(t, self.debug_history['dRcb_dt'], label='dRcb_dt')
        plt.plot(t, self.debug_history['dRcf_dt'], label='dRcf_dt')
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel("time, s")
        plt.ylabel("Radius change rate, m/s")
        plt.title("Radius change rate vs time")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{save_dir}/dR_dt_vs_time.png")
        plt.close()
        
        # 绘制气体浓度变化率随时间的变化
        plt.figure(figsize=(10, 6))
        plt.plot(t, self.debug_history['dCgb_dt'], label='dCgb_dt')
        plt.plot(t, self.debug_history['dCgf_dt'], label='dCgf_dt')
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel("time, s")
        plt.ylabel("dCgb/dt, (1/m³/s)")
        plt.title("dCgb/dt vs time")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{save_dir}/dCg_dt_vs_time.png")
        plt.close()