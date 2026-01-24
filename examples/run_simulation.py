import numpy as np
import matplotlib.pyplot as plt
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters
import logging
import os

# 配置日志
# Note: This script now supports adaptive time stepping. To enable it, set adaptive_stepping=True
# when calling run_test4() or set adaptive_stepping = True in the __main__ block below.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='test4_run_lsoda.log',
    filemode='w'
)
logger = logging.getLogger('test4_run_euler')

def run_test4(sim_time=7200000, dt=None, max_dt=None, max_steps=1000000, output_interval=1000,
              save_path='test4_results.png', debug_plots_dir='test4_debug_plots/', adaptive_stepping=False):
    """
    运行测试4，优化气泡半径演化逻辑，重点关注表面能与气体压力平衡关系

    参数:
        sim_time: 模拟时间（秒），默认为360秒（6分钟）
        dt: Euler方法的初始时间步长（秒），如果为None则使用参数中的默认值
        max_dt: Euler方法的最大时间步长（秒），如果为None则使用参数中的默认值
        max_steps: 最大计算步数，默认为1000000步
        output_interval: 状态输出的步数间隔，默认每1000步输出一次
        save_path: 结果图表保存路径
        debug_plots_dir: 调试图表保存目录
        adaptive_stepping: 是否启用自适应时间步长（默认False）
    """
    logger.info(f"======== 测试4开始 ========")
    logger.info(f"模拟参数: 模拟时间={sim_time}秒, 最大步数={max_steps}步, 自适应步长={adaptive_stepping}")
    
    # 创建参数
    params = create_default_parameters()
    
    # 使用测试3的参数设置作为基础
    params['time_step'] = 1e-9  # 初始时间步长保持相同
    params['max_time_step'] = 0.1  # 最大时间步长与测试3相同
    params['temperature'] = 650  # 温度
    params['Fnb'] = 1e-5  # 基体气泡成核因子
    params['Fnf'] = 1e-5  # 界面气泡成核因子
    params['dislocation_density'] = 7.0e13  # 位错密度, 单位：m^-2
    params['surface_energy'] = 0.5  # 表面能
    params['resolution_rate'] = 2.0e-5  # 重溶率 s^-1
    
    # 增大气体扩散系数
    params['Dgb_prefactor'] = 8.55e-12  # 晶内扩散系数前因子
    params['Dgb_fission_term'] = 1.0e-40  # 裂变相关项系数
    
    # 相界扩散系数倍率
    params['Dgf_multiplier'] = 1e0  # 1倍
    
    # 提高空位扩散系数
    params['Dv0'] = 7.767e-8  # 空位扩散系数前因子
    params['Di0'] = 1.28  # 空位迁移能
    params['Eim'] = 1.24  # 间隙原子迁移能  
    params['Evfmuti'] = 1.0   
    
    # 裂变率和气体生成率
    params['fission_rate'] = 5e19  # 裂变率
    params['gas_production_rate'] = 0.5  # 气体生成率因子
    
    # 新增参数用于优化气泡半径演化
    params['critical_radius'] = 50e-9  # 临界半径，单位：m
    params['radius_smoothing_factor'] = 0.8  # 半径演化平滑因子
    params['pressure_scaling_factor'] = 0.5  # 小气泡内压力缩放因子
    params['vacancy_contribution_weight'] = 1.2  # 空位贡献项权重

    # 自适应步长控制参数
    params['adaptive_stepping_enabled'] = adaptive_stepping
    if adaptive_stepping:
        params['rtol'] = 1e-6  # 相对误差容限
        params['atol'] = 1e-9  # 绝对误差容限
        params['min_step'] = 1e-12  # 最小时间步长
        params['max_step'] = sim_time / 10  # 最大时间步长
        logger.info(f"启用自适应步长控制: rtol={params['rtol']}, atol={params['atol']}")

    # 记录使用的参数
    logger.info("使用测试4的参数设置:")
    logger.info(f"- 温度: {params['temperature']}K")
    logger.info(f"- 初始时间步长: {params['time_step']}s")
    logger.info(f"- 最大时间步长: {params['max_time_step']}s")
    logger.info(f"- 位错密度: {params['dislocation_density']}m^-2")
    logger.info(f"- 表面能: {params['surface_energy']}J/m^2")
    logger.info(f"- 气泡成核因子 Fnb: {params['Fnb']}, Fnf: {params['Fnf']}")
    logger.info(f"- 重溶率: {params['resolution_rate']}m^-3")
    logger.info(f"- 气体扩散系数前因子: {params['Dgb_prefactor']}")
    logger.info(f"- 裂变相关项系数: {params['Dgb_fission_term']}")
    logger.info(f"- 相界扩散系数倍率: {params['Dgf_multiplier']}")
    logger.info(f"- 空位扩散系数前因子: {params['Dv0']}")
    logger.info(f"- 空位迁移能: {params['Evm']}eV")
    logger.info(f"- 裂变率: {params['fission_rate']}")
    logger.info(f"- 气体生成率因子: {params['gas_production_rate']}")
    logger.info(f"- 临界半径: {params['critical_radius']}m")
    logger.info(f"- 半径演化平滑因子: {params['radius_smoothing_factor']}")
    logger.info(f"- 小气泡内压力缩放因子: {params['pressure_scaling_factor']}")
    logger.info(f"- 空位贡献项权重: {params['vacancy_contribution_weight']}")
    
    # 如果指定了时间步长参数，则覆盖默认值
    if dt is not None:
        params['time_step'] = dt
        logger.info(f"使用指定的初始时间步长: {dt}秒")
    else:
        dt = params['time_step']
        logger.info(f"使用默认初始时间步长: {dt}秒")
        
    if max_dt is not None:
        params['max_time_step'] = max_dt
        logger.info(f"使用指定的最大时间步长: {max_dt}秒")
    else:
        max_dt = params['max_time_step']
        logger.info(f"使用默认最大时间步长: {max_dt}秒")
    
    # 创建修改过的Euler模型 - 修改初始气泡内气体原子数为0.1
    model = GasSwellingModel(params)
    # 手动修改初始气泡内气体原子数
    model.initial_state[2] = 4.0  # Ncb (每个基体气泡内气体原子数)
    model.initial_state[6] = 4.0  # Ncf (每个界面气泡内气体原子数)
    logger.info(f"初始气泡内气体原子数已修改为: 4.0")
    
    # 设置时间点
    t_eval = np.linspace(0, sim_time, 100)  # 保持计算点数为100
    
    # 确保调试图表目录存在
    if not os.path.exists(debug_plots_dir):
        os.makedirs(debug_plots_dir)
        logger.info(f"创建调试图表目录: {debug_plots_dir}")
    
    try:
        logger.info("开始LSODA方法求解...")
        # 添加自适应时间步长支持和状态输出间隔
        result = model.solve(
            t_span=(0, sim_time),
            t_eval=t_eval,
#            dt=dt,
#            max_dt=max_dt,
#            max_steps=max_steps,
#            output_interval=output_interval
        )
        logger.info(f"Euler方法求解完成，总步数: {model.step_count}")
        
        # 计算肿胀率
        Rcb = result['Rcb']
        Rcf = result['Rcf']
        Ccb = result['Ccb']
        Ccf = result['Ccf']
        
        V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
        total_V_bubble = V_bubble_b + V_bubble_f
        swelling = total_V_bubble * 100  # 肿胀率（百分比）
        
        # 输出关键信息
        logger.info(f"模拟结束时间: {result['time'][-1]:.2f}秒")
        logger.info(f"最终基体气泡半径: {Rcb[-1]*1e9:.4f} nm")
        logger.info(f"最终界面气泡半径: {Rcf[-1]*1e9:.4f} nm")
        logger.info(f"最终肿胀率: {swelling[-1]:.6f}%")
        
        # 计算气泡半径增长率
        initial_Rcb = Rcb[0]
        final_Rcb = Rcb[-1]
        if initial_Rcb > 0:
            Rcb_growth_ratio = final_Rcb / initial_Rcb
            Rcb_growth_percent = (Rcb_growth_ratio - 1) * 100
            logger.info(f"基体气泡半径增长比例: {Rcb_growth_ratio:.4f} (增长了 {Rcb_growth_percent:.2f}%)")
        
        initial_Rcf = Rcf[0]
        final_Rcf = Rcf[-1]
        if initial_Rcf > 0:
            Rcf_growth_ratio = final_Rcf / initial_Rcf
            Rcf_growth_percent = (Rcf_growth_ratio - 1) * 100
            logger.info(f"界面气泡半径增长比例: {Rcf_growth_ratio:.4f} (增长了 {Rcf_growth_percent:.2f}%)")
        
        # 计算气体分配情况
        total_gas_initial = model.initial_state[0] + model.initial_state[4] + \
                          model.initial_state[1] * model.initial_state[2] + \
                          model.initial_state[5] * model.initial_state[6]
        
        total_gas_final = result['Cgb'][-1] + result['Cgf'][-1] + \
                         result['Ccb'][-1] * result['Ncb'][-1] + \
                         result['Ccf'][-1] * result['Ncf'][-1] + \
                         result['released_gas'][-1]
        
        gas_in_bulk = result['Cgb'][-1]
        gas_in_bulk_bubbles = result['Ccb'][-1] * result['Ncb'][-1]
        gas_in_interface = result['Cgf'][-1]
        gas_in_interface_bubbles = result['Ccf'][-1] * result['Ncf'][-1]
        gas_released = result['released_gas'][-1]
        
        logger.info(f"气体分配情况:")
        logger.info(f"- 初始总气体量: {total_gas_initial:.4e} atoms/m³")
        logger.info(f"- 最终总气体量: {total_gas_final:.4e} atoms/m³")
        logger.info(f"- 基体中气体: {gas_in_bulk:.4e} atoms/m³ ({gas_in_bulk/total_gas_final*100:.2f}%)")
        logger.info(f"- 基体气泡中气体: {gas_in_bulk_bubbles:.4e} atoms/m³ ({gas_in_bulk_bubbles/total_gas_final*100:.2f}%)")
        logger.info(f"- 界面中气体: {gas_in_interface:.4e} atoms/m³ ({gas_in_interface/total_gas_final*100:.2f}%)")
        logger.info(f"- 界面气泡中气体: {gas_in_interface_bubbles:.4e} atoms/m³ ({gas_in_interface_bubbles/total_gas_final*100:.2f}%)")
        logger.info(f"- 释放的气体: {gas_released:.4e} atoms/m³ ({gas_released/total_gas_final*100:.2f}%)")
        
        # 输出气体压力等关键诊断信息
        if 'Pg_b' in model.debug_history and len(model.debug_history['Pg_b']) > 0:
            final_pg_b = model.debug_history['Pg_b'][-1]
            final_pg_f = model.debug_history['Pg_f'][-1]
            logger.info(f"最终基体气泡内压: {final_pg_b:.4e} Pa")
            logger.info(f"最终界面气泡内压: {final_pg_f:.4e} Pa")
        
        # 绘制并保存结果到指定路径
        plot_results(result, swelling, save_path=save_path)
        
        # 绘制调试历史数据并保存到指定目录
        model.plot_debug_history(save_dir=debug_plots_dir)
        
        logger.info(f"======== 测试4完成 ========")
        logger.info(f"已完成的步数: {model.step_count}")
        logger.info(f"结果已保存到: {save_path}")
        logger.info(f"调试图表已保存到: {debug_plots_dir}")
        return result, swelling
        
    except Exception as e:
        logger.error(f"求解过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def plot_results(result, swelling, save_path='test4_results.png'):
    """绘制计算结果并保存到指定路径"""
    time_minutes = result['time'] / 60  # 转换为分钟
    Burnup = 0.9/4176980*time_minutes*60
    # 创建一个4x2的子图布局
    fig, axs = plt.subplots(2, 4, figsize=(30, 10))
    
    # 气泡半径随时间变化 
    axs[0, 0].plot(Burnup, result['Rcb']*1e9, label='Bulk Bubble')
    axs[0, 0].plot(Burnup, result['Rcf']*1e9, label='Interface Bubble')
    axs[0, 0].set_xlabel('Burnup (%Fima)')
    axs[0, 0].set_ylabel('Bubble Radius (nm)')
    axs[0, 0].set_title('Bubble Radius vs Burnup')
    axs[0, 0].legend()
    axs[0, 0].grid(True)
    
    # 肿胀率随时间变化
    axs[0, 1].plot(Burnup, swelling)
    axs[0, 1].set_xlabel('Burnup (%Fima)')
    axs[0, 1].set_ylabel('Swelling Rate (%)')
    axs[0, 1].set_title('Swelling Rate vs Burnup')
    axs[0, 1].grid(True)
    
    # 气体浓度随时间变化
    axs[1, 0].plot(Burnup, result['Cgb'], label='Bulk Gas Concentration')
    axs[1, 0].plot(Burnup, result['Cgf'], label='Interface Gas Concentration')
    axs[1, 0].set_xlabel('Burnup (%Fima)')
    axs[1, 0].set_ylabel('Gas Concentration (atoms/m³)')
    axs[1, 0].set_title('Gas Concentration vs Burnup')
    axs[1, 0].legend()
    axs[1, 0].grid(True)
    
    # 气泡浓度随时间变化
    axs[1, 1].plot(Burnup, result['Ccb'], label='Bulk Bubble Concentration')
    axs[1, 1].plot(Burnup, result['Ccf'], label='Interface Bubble Concentration')
    axs[1, 1].set_xlabel('Burnup (%Fima)')
    axs[1, 1].set_ylabel('Bubble Concentration (cavities/m³)')
    axs[1, 1].set_title('Bubble Concentration vs Burnup')
    axs[1, 1].legend()
    axs[1, 1].grid(True)
    
    # 气泡内气体原子数随时间变化
    axs[0, 2].semilogy(Burnup, result['Ncb'], label='Gas Atoms in Bulk Bubble')
    axs[0, 2].semilogy(Burnup, result['Ncf'], label='Gas Atoms in Interface Bubble')
    axs[0, 2].set_xlabel('Burnup (%Fima)')
    axs[0, 2].set_ylabel('Gas Atoms (atoms/cavity)')
    axs[0, 2].set_title('Gas Atoms per Bubble vs Burnup')
    axs[0, 2].legend()
    axs[0, 2].grid(True)
    
    # 空位浓度随时间变化
    axs[0, 3].semilogy(Burnup, result['cvb'], label='Bulk Vacancy Concentration')
    axs[0, 3].semilogy(Burnup, result['cvf'], label='Interface Vacancy Concentration')
    axs[0, 3].set_xlabel('Burnup (%Fima)')
    axs[0, 3].set_ylabel('Vacancy Concentration')
    axs[0, 3].set_title('Vacancy Concentration vs Burnup')
    axs[0, 3].legend()
    axs[0, 3].grid(True)
    
    # 间隙原子浓度随时间变化
    axs[1, 2].semilogy(Burnup, result['cib'], label='Bulk Interstitial Concentration')
    axs[1, 2].semilogy(Burnup, result['cif'], label='Interface Interstitial Concentration')
    axs[1, 2].set_xlabel('Burnup (%Fima)')
    axs[1, 2].set_ylabel('Interstitial Concentration')
    axs[1, 2].set_title('Interstitial Concentration vs Burnup')
    axs[1, 2].legend()
    axs[1, 2].grid(True)
    
    # 气体释放量随时间变化
    axs[1, 3].plot(Burnup, result['released_gas'])
    axs[1, 3].set_xlabel('Burnup (%Fima)')
    axs[1, 3].set_ylabel('Released Gas')
    axs[1, 3].set_title('Released Gas vs Burnup')
    axs[1, 3].grid(True)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    logger.info(f"Results chart saved to: {save_path}")

def analyze_test_results():
    """比较测试3和测试4的结果，分析优化气泡半径演化方程的效果"""
    logger.info("开始分析测试3和测试4的结果...")
    
    try:
        # 打印测试3结果摘要
        logger.info("测试3结果摘要:")
        
        if os.path.exists("test3_run_euler.log"):
            with open("test3_run_euler.log", 'r') as f:
                lines = f.readlines()
                # 提取关键结果行
                test3_results = [line for line in lines if "最终" in line or "肿胀率" in line or "半径增长" in line]
                for line in test3_results:
                    logger.info(f"测试3: {line.strip()}")
        else:
            logger.warning("未找到测试3日志文件: test3_run_euler.log")
            
        # 已经有了测试4的结果，可以在这里添加测试3和测试4的对比分析
        logger.info("气泡半径演化优化效果分析:")
        logger.info("1. 气泡半径变化: 对比测试3和测试4中气泡半径的增长情况")
        logger.info("2. 气体压力变化: 分析改进后的气体压力是否更加合理")
        logger.info("3. 小气泡处理: 评估引入临界半径概念对小气泡处理的效果")
        logger.info("4. 表面能与气体压力平衡: 分析优化后的平衡关系是否更合理")
        logger.info("5. 数值稳定性: 评估改进后的计算稳定性是否提高")
        
        # 详细比较将在测试4运行后补充
        logger.info("详细比较结果将在测试4运行完成后在日志中提供")
        
    except Exception as e:
        logger.error(f"分析测试结果时出错: {str(e)}")

if __name__ == "__main__":
    print("开始运行辐射气体气泡肿胀模型 - 测试4（优化气泡半径演化逻辑）")
    logger.info("======== 程序启动 ========")

    # 获取并修改参数
    params = create_default_parameters()

    # 自适应步长控制（可选，默认关闭以保持向后兼容）
    adaptive_stepping = False  # 设置为 True 启用自适应步长

    # 模拟时间为6分钟
    sim_time = 7200000*5#4176980#7200000  # 秒
    
    # 设置测试4使用的参数
    params['time_step'] = 1e-9  # 初始时间步长
    params['max_time_step'] = 100.0  # 最大时间步长
    #params['temperature'] = 600  # 温度800K
    params['Fnb'] = 1e-5  # 基体气泡成核因子
    params['Fnf'] = 1e-5  # 界面气泡成核因子
    params['dislocation_density'] =7.0e13  # 位错密度
    params['surface_energy'] = 0.5  # 表面能
    params['resolution_rate'] = 2e-5  # 重溶率
    
    # 增大气体扩散系数
    params['Dgb_prefactor'] = 8.55e-10  # 晶内扩散系数前因子
    params['Dgb_fission_term'] = 1.0e-40  # 裂变相关项系数
    
    # 相界扩散系数倍率
    params['Dgf_multiplier'] = 1e0  # 10万倍
    
    # 提高空位扩散系数
    #params['Dv0'] = 7.767e-11  # 空位扩散系数前因子
    #params['Evm'] = 0.434  # 空位迁移能
   # params['Eim'] = 0.42  # 间隙原子迁移能 
    #params['Evfmuti'] = 1.0
    # 裂变率和气体生成率
    params['fission_rate'] = 5e19  # 裂变率
    params['gas_production_rate'] = 0.5  # 气体生成率因子
    
    # 新增参数用于优化气泡半径演化
    params['critical_radius'] = 2e-9  # 临界半径，单位：m
    params['radius_smoothing_factor'] = 0.8  # 半径演化平滑因子
    params['pressure_scaling_factor'] = 0.5  # 小气泡内压力缩放因子
    params['vacancy_contribution_weight'] = 1.2  # 空位贡献项权重
    
    # 增加最大步数，以便能够模拟足够长的物理时间
    max_steps = 1000000  # 100万步
    
    print(f"测试4参数设置:")
    print(f"- 温度: {params['temperature']}K")
    print(f"- 表面能: {params['surface_energy']}J/m^2")
    print(f"- 临界半径: {params['critical_radius']*1e9} nm")
    print(f"- 半径演化平滑因子: {params['radius_smoothing_factor']}")
    print(f"- 小气泡内压力缩放因子: {params['pressure_scaling_factor']}")
    print(f"- 空位贡献项权重: {params['vacancy_contribution_weight']}")
    print(f"- 最大计算步数: {max_steps}步")
    print(f"- 模拟时间: {sim_time}秒")
    print(f"- 优化目标: 改进气泡半径演化逻辑，特别是小气泡的处理")
    print(f"- 自适应步长: {adaptive_stepping}")

    logger.info("开始执行测试4（优化气泡半径演化逻辑）")
    # 运行测试4
    result, swelling = run_test4(
        sim_time=sim_time,
        dt=params['time_step'],
        max_dt=params['max_time_step'],
        max_steps=max_steps,
        output_interval=1000,  # 每1000步输出一次详细状态
        save_path='test4_results.png',
        debug_plots_dir='test4_debug_plots/',
        adaptive_stepping=adaptive_stepping  # 传递自适应步长参数
    )
    
    # 分析测试结果
    if result is not None:
        analyze_test_results()  # 比较测试3和测试4的结果
    
    print("测试4完成")
    logger.info("======== 程序正常结束 ========")


import numpy as np
import matplotlib.pyplot as plt
from models.euler_model import EulerGasSwellingModel
from params.parameters import create_default_parameters
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='test4_run_euler.log',
    filemode='w'
)
logger = logging.getLogger('test4_run_euler')

def run_test4(sim_time=120000, dt=None, max_dt=None, max_steps=1000000, output_interval=1000,
              save_path='test4_results_euler.png', debug_plots_dir='test4_debug_euler_plots/'):
    """
    运行测试4，优化气泡半径演化逻辑，重点关注表面能与气体压力平衡关系
    
    参数:
        sim_time: 模拟时间（秒），默认为360秒（6分钟）
        dt: Euler方法的初始时间步长（秒），如果为None则使用参数中的默认值
        max_dt: Euler方法的最大时间步长（秒），如果为None则使用参数中的默认值
        max_steps: 最大计算步数，默认为1000000步
        output_interval: 状态输出的步数间隔，默认每1000步输出一次
        save_path: 结果图表保存路径
        debug_plots_dir: 调试图表保存目录
    """
    logger.info(f"======== 测试4开始 ========")
    logger.info(f"模拟参数: 模拟时间={sim_time}秒, 最大步数={max_steps}步")
    
    # 创建参数
    params = create_default_parameters()
    
    # 使用测试3的参数设置作为基础
    params['time_step'] = 1e-9  # 初始时间步长保持相同
    params['max_time_step'] = 0.1  # 最大时间步长与测试3相同
    params['temperature'] = 673  # 温度
    params['Fnb'] = 1e-5  # 基体气泡成核因子
    params['Fnf'] = 1e-5  # 界面气泡成核因子
    params['dislocation_density'] = 7.0e13  # 位错密度, 单位：m^-2
    params['surface_energy'] = 0.5  # 表面能
    params['resolution_rate'] = 2.0e-5  # 重溶率 s^-1
    
    # 增大气体扩散系数
    params['Dgb_prefactor'] = 8.55e-12  # 晶内扩散系数前因子
    params['Dgb_fission_term'] = 1.0e-40  # 裂变相关项系数
    
    # 相界扩散系数倍率
    params['Dgf_multiplier'] = 1e0  # 1倍
    
    # 提高空位扩散系数
    params['Dv0'] = 7.767e-13  # 空位扩散系数前因子
    params['Di0'] = 1.259e-12
    params['Evm'] = 0.434  # 空位迁移能
    params['Eim'] = 0.42  # 间隙原子迁移能  
    
    # 裂变率和气体生成率
    params['fission_rate'] = 5e19  # 裂变率
    params['gas_production_rate'] = 0.5  # 气体生成率因子
    
    # 新增参数用于优化气泡半径演化
    params['critical_radius'] = 50e-9  # 临界半径，单位：m
    params['radius_smoothing_factor'] = 0.8  # 半径演化平滑因子
    params['pressure_scaling_factor'] = 0.5  # 小气泡内压力缩放因子
    params['vacancy_contribution_weight'] = 1.2  # 空位贡献项权重

    # 自适应步长控制参数
    params['adaptive_stepping_enabled'] = adaptive_stepping
    if adaptive_stepping:
        params['rtol'] = 1e-6  # 相对误差容限
        params['atol'] = 1e-9  # 绝对误差容限
        params['min_step'] = 1e-12  # 最小时间步长
        params['max_step'] = sim_time / 10  # 最大时间步长
        logger.info(f"启用自适应步长控制: rtol={params['rtol']}, atol={params['atol']}")

    # 记录使用的参数
    logger.info("使用测试4的参数设置:")
    logger.info(f"- 温度: {params['temperature']}K")
    logger.info(f"- 初始时间步长: {params['time_step']}s")
    logger.info(f"- 最大时间步长: {params['max_time_step']}s")
    logger.info(f"- 位错密度: {params['dislocation_density']}m^-2")
    logger.info(f"- 表面能: {params['surface_energy']}J/m^2")
    logger.info(f"- 气泡成核因子 Fnb: {params['Fnb']}, Fnf: {params['Fnf']}")
    logger.info(f"- 重溶率: {params['resolution_rate']}m^-3")
    logger.info(f"- 气体扩散系数前因子: {params['Dgb_prefactor']}")
    logger.info(f"- 裂变相关项系数: {params['Dgb_fission_term']}")
    logger.info(f"- 相界扩散系数倍率: {params['Dgf_multiplier']}")
    logger.info(f"- 空位扩散系数前因子: {params['Dv0']}")
    logger.info(f"- 空位迁移能: {params['Evm']}eV")
    logger.info(f"- 裂变率: {params['fission_rate']}")
    logger.info(f"- 气体生成率因子: {params['gas_production_rate']}")
    logger.info(f"- 临界半径: {params['critical_radius']}m")
    logger.info(f"- 半径演化平滑因子: {params['radius_smoothing_factor']}")
    logger.info(f"- 小气泡内压力缩放因子: {params['pressure_scaling_factor']}")
    logger.info(f"- 空位贡献项权重: {params['vacancy_contribution_weight']}")
    
    # 如果指定了时间步长参数，则覆盖默认值
    if dt is not None:
        params['time_step'] = dt
        logger.info(f"使用指定的初始时间步长: {dt}秒")
    else:
        dt = params['time_step']
        logger.info(f"使用默认初始时间步长: {dt}秒")
        
    if max_dt is not None:
        params['max_time_step'] = max_dt
        logger.info(f"使用指定的最大时间步长: {max_dt}秒")
    else:
        max_dt = params['max_time_step']
        logger.info(f"使用默认最大时间步长: {max_dt}秒")
    
    # 创建修改过的Euler模型 - 修改初始气泡内气体原子数为0.1
    model = EulerGasSwellingModel(params)
    # 手动修改初始气泡内气体原子数
    model.initial_state[2] = 4.0  # Ncb (每个基体气泡内气体原子数)
    model.initial_state[6] = 4.0  # Ncf (每个界面气泡内气体原子数)
    logger.info(f"初始气泡内气体原子数已修改为: 4.0")
    
    # 设置时间点
    t_eval = np.linspace(0, sim_time, 100)  # 保持计算点数为100
    
    # 确保调试图表目录存在
    if not os.path.exists(debug_plots_dir):
        os.makedirs(debug_plots_dir)
        logger.info(f"创建调试图表目录: {debug_plots_dir}")
    
    try:
        logger.info("开始Euler方法求解...")
        # 添加自适应时间步长支持和状态输出间隔
        result = model.euler_solve(
            t_span=(0, sim_time),
            t_eval=t_eval,
            dt=dt,
            max_dt=max_dt,
            max_steps=max_steps,
            output_interval=output_interval
        )
        logger.info(f"Euler方法求解完成，总步数: {model.step_count}")
        
        # 计算肿胀率
        Rcb = result['Rcb']
        Rcf = result['Rcf']
        Ccb = result['Ccb']
        Ccf = result['Ccf']
        
        V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
        V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
        total_V_bubble = V_bubble_b + V_bubble_f
        swelling = total_V_bubble * 100  # 肿胀率（百分比）
        
        # 输出关键信息
        logger.info(f"模拟结束时间: {result['time'][-1]:.2f}秒")
        logger.info(f"最终基体气泡半径: {Rcb[-1]*1e9:.4f} nm")
        logger.info(f"最终界面气泡半径: {Rcf[-1]*1e9:.4f} nm")
        logger.info(f"最终肿胀率: {swelling[-1]:.6f}%")
        
        # 计算气泡半径增长率
        initial_Rcb = Rcb[0]
        final_Rcb = Rcb[-1]
        if initial_Rcb > 0:
            Rcb_growth_ratio = final_Rcb / initial_Rcb
            Rcb_growth_percent = (Rcb_growth_ratio - 1) * 100
            logger.info(f"基体气泡半径增长比例: {Rcb_growth_ratio:.4f} (增长了 {Rcb_growth_percent:.2f}%)")
        
        initial_Rcf = Rcf[0]
        final_Rcf = Rcf[-1]
        if initial_Rcf > 0:
            Rcf_growth_ratio = final_Rcf / initial_Rcf
            Rcf_growth_percent = (Rcf_growth_ratio - 1) * 100
            logger.info(f"界面气泡半径增长比例: {Rcf_growth_ratio:.4f} (增长了 {Rcf_growth_percent:.2f}%)")
        
        # 计算气体分配情况
        total_gas_initial = model.initial_state[0] + model.initial_state[4] + \
                          model.initial_state[1] * model.initial_state[2] + \
                          model.initial_state[5] * model.initial_state[6]
        
        total_gas_final = result['Cgb'][-1] + result['Cgf'][-1] + \
                         result['Ccb'][-1] * result['Ncb'][-1] + \
                         result['Ccf'][-1] * result['Ncf'][-1] + \
                         result['released_gas'][-1]
        
        gas_in_bulk = result['Cgb'][-1]
        gas_in_bulk_bubbles = result['Ccb'][-1] * result['Ncb'][-1]
        gas_in_interface = result['Cgf'][-1]
        gas_in_interface_bubbles = result['Ccf'][-1] * result['Ncf'][-1]
        gas_released = result['released_gas'][-1]
        
        logger.info(f"气体分配情况:")
        logger.info(f"- 初始总气体量: {total_gas_initial:.4e} atoms/m³")
        logger.info(f"- 最终总气体量: {total_gas_final:.4e} atoms/m³")
        logger.info(f"- 基体中气体: {gas_in_bulk:.4e} atoms/m³ ({gas_in_bulk/total_gas_final*100:.2f}%)")
        logger.info(f"- 基体气泡中气体: {gas_in_bulk_bubbles:.4e} atoms/m³ ({gas_in_bulk_bubbles/total_gas_final*100:.2f}%)")
        logger.info(f"- 界面中气体: {gas_in_interface:.4e} atoms/m³ ({gas_in_interface/total_gas_final*100:.2f}%)")
        logger.info(f"- 界面气泡中气体: {gas_in_interface_bubbles:.4e} atoms/m³ ({gas_in_interface_bubbles/total_gas_final*100:.2f}%)")
        logger.info(f"- 释放的气体: {gas_released:.4e} atoms/m³ ({gas_released/total_gas_final*100:.2f}%)")
        
        # 输出气体压力等关键诊断信息
        if 'Pg_b' in model.debug_history and len(model.debug_history['Pg_b']) > 0:
            final_pg_b = model.debug_history['Pg_b'][-1]
            final_pg_f = model.debug_history['Pg_f'][-1]
            logger.info(f"最终基体气泡内压: {final_pg_b:.4e} Pa")
            logger.info(f"最终界面气泡内压: {final_pg_f:.4e} Pa")
        
        # 绘制并保存结果到指定路径
        plot_results(result, swelling, save_path=save_path)
        
        # 绘制调试历史数据并保存到指定目录
        model.plot_debug_history(save_dir=debug_plots_dir)
        
        logger.info(f"======== 测试4完成 ========")
        logger.info(f"已完成的步数: {model.step_count}")
        logger.info(f"结果已保存到: {save_path}")
        logger.info(f"调试图表已保存到: {debug_plots_dir}")
        return result, swelling
        
    except Exception as e:
        logger.error(f"求解过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def plot_results(result, swelling, save_path='test4_results_euler.png'):
    """绘制计算结果并保存到指定路径"""
    time_minutes = result['time'] / 60  # 转换为分钟
    
    # 创建一个4x2的子图布局
    fig, axs = plt.subplots(2, 4, figsize=(30, 10))
    
    # 气泡半径随时间变化 
    axs[0, 0].plot(time_minutes, result['Rcb']*1e9, label='Bulk Bubble')
    axs[0, 0].plot(time_minutes, result['Rcf']*1e9, label='Interface Bubble')
    axs[0, 0].set_xlabel('Time (minutes)')
    axs[0, 0].set_ylabel('Bubble Radius (nm)')
    axs[0, 0].set_title('Bubble Radius vs Time')
    axs[0, 0].legend()
    axs[0, 0].grid(True)
    
    # 肿胀率随时间变化
    axs[0, 1].plot(time_minutes, swelling)
    axs[0, 1].set_xlabel('Time (minutes)')
    axs[0, 1].set_ylabel('Swelling Rate (%)')
    axs[0, 1].set_title('Swelling Rate vs Time')
    axs[0, 1].grid(True)
    
    # 气体浓度随时间变化
    axs[1, 0].plot(time_minutes, result['Cgb'], label='Bulk Gas Concentration')
    axs[1, 0].plot(time_minutes, result['Cgf'], label='Interface Gas Concentration')
    axs[1, 0].set_xlabel('Time (minutes)')
    axs[1, 0].set_ylabel('Gas Concentration (atoms/m³)')
    axs[1, 0].set_title('Gas Concentration vs Time')
    axs[1, 0].legend()
    axs[1, 0].grid(True)
    
    # 气泡浓度随时间变化
    axs[1, 1].plot(time_minutes, result['Ccb'], label='Bulk Bubble Concentration')
    axs[1, 1].plot(time_minutes, result['Ccf'], label='Interface Bubble Concentration')
    axs[1, 1].set_xlabel('Time (minutes)')
    axs[1, 1].set_ylabel('Bubble Concentration (cavities/m³)')
    axs[1, 1].set_title('Bubble Concentration vs Time')
    axs[1, 1].legend()
    axs[1, 1].grid(True)
    
    # 气泡内气体原子数随时间变化
    axs[0, 2].plot(time_minutes, result['Ncb'], label='Gas Atoms in Bulk Bubble')
    axs[0, 2].plot(time_minutes, result['Ncf'], label='Gas Atoms in Interface Bubble')
    axs[0, 2].set_xlabel('Time (minutes)')
    axs[0, 2].set_ylabel('Gas Atoms (atoms/cavity)')
    axs[0, 2].set_title('Gas Atoms per Bubble vs Time')
    axs[0, 2].legend()
    axs[0, 2].grid(True)
    
    # 空位浓度随时间变化
    axs[0, 3].semilogy(time_minutes, result['cvb'], label='Bulk Vacancy Concentration')
    axs[0, 3].semilogy(time_minutes, result['cvf'], label='Interface Vacancy Concentration')
    axs[0, 3].set_xlabel('Time (minutes)')
    axs[0, 3].set_ylabel('Vacancy Concentration')
    axs[0, 3].set_title('Vacancy Concentration vs Time')
    axs[0, 3].legend()
    axs[0, 3].grid(True)
    
    # 间隙原子浓度随时间变化
    axs[1, 2].semilogy(time_minutes, result['cib'], label='Bulk Interstitial Concentration')
    axs[1, 2].semilogy(time_minutes, result['cif'], label='Interface Interstitial Concentration')
    axs[1, 2].set_xlabel('Time (minutes)')
    axs[1, 2].set_ylabel('Interstitial Concentration')
    axs[1, 2].set_title('Interstitial Concentration vs Time')
    axs[1, 2].legend()
    axs[1, 2].grid(True)
    
    # 气体释放量随时间变化
    axs[1, 3].plot(time_minutes, result['released_gas'])
    axs[1, 3].set_xlabel('Time (minutes)')
    axs[1, 3].set_ylabel('Released Gas')
    axs[1, 3].set_title('Released Gas vs Time')
    axs[1, 3].grid(True)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    logger.info(f"Results chart saved to: {save_path}")

def analyze_test_results():
    """比较测试3和测试4的结果，分析优化气泡半径演化方程的效果"""
    logger.info("开始分析测试3和测试4的结果...")
    
    try:
        # 打印测试3结果摘要
        logger.info("测试3结果摘要:")
        
        if os.path.exists("test3_run_euler.log"):
            with open("test3_run_euler.log", 'r') as f:
                lines = f.readlines()
                # 提取关键结果行
                test3_results = [line for line in lines if "最终" in line or "肿胀率" in line or "半径增长" in line]
                for line in test3_results:
                    logger.info(f"测试3: {line.strip()}")
        else:
            logger.warning("未找到测试3日志文件: test3_run_euler.log")
            
        # 已经有了测试4的结果，可以在这里添加测试3和测试4的对比分析
        logger.info("气泡半径演化优化效果分析:")
        logger.info("1. 气泡半径变化: 对比测试3和测试4中气泡半径的增长情况")
        logger.info("2. 气体压力变化: 分析改进后的气体压力是否更加合理")
        logger.info("3. 小气泡处理: 评估引入临界半径概念对小气泡处理的效果")
        logger.info("4. 表面能与气体压力平衡: 分析优化后的平衡关系是否更合理")
        logger.info("5. 数值稳定性: 评估改进后的计算稳定性是否提高")
        
        # 详细比较将在测试4运行后补充
        logger.info("详细比较结果将在测试4运行完成后在日志中提供")
        
    except Exception as e:
        logger.error(f"分析测试结果时出错: {str(e)}")

if __name__ == "__main__":
    print("开始运行辐射气体气泡肿胀Euler模型 - 测试4（优化气泡半径演化逻辑）")
    logger.info("======== 程序启动 ========")
    
    # 获取并修改参数
    params = create_default_parameters()
    
    # 模拟时间为6分钟
    sim_time = 7200000  # 秒
    
    # 设置测试4使用的参数
    params['time_step'] = 1e-9  # 初始时间步长
    params['max_time_step'] = 100.0  # 最大时间步长
    params['temperature'] = 673  # 温度800K
    params['Fnb'] = 1e-5  # 基体气泡成核因子
    params['Fnf'] = 1e-5  # 界面气泡成核因子
    params['dislocation_density'] = 4.0e13  # 位错密度
    params['surface_energy'] = 0.5  # 表面能
    params['resolution_rate'] = 2e-5  # 重溶率
    
    # 增大气体扩散系数
    params['Dgb_prefactor'] = 8.55e-12  # 晶内扩散系数前因子
    params['Dgb_fission_term'] = 1.0e-40  # 裂变相关项系数
    
    # 相界扩散系数倍率
    params['Dgf_multiplier'] = 1e0  # 10万倍
    
    # 提高空位扩散系数
    params['Dv0'] = 7.767e-13  # 空位扩散系数前因子
    params['Evm'] = 0.434  # 空位迁移能
    params['Eim'] = 0.42  # 间隙原子迁移能    
    # 裂变率和气体生成率
    params['fission_rate'] = 5e19  # 裂变率
    params['gas_production_rate'] = 0.25  # 气体生成率因子
    
    # 新增参数用于优化气泡半径演化
    params['critical_radius'] = 2e-9  # 临界半径，单位：m
    params['radius_smoothing_factor'] = 0.8  # 半径演化平滑因子
    params['pressure_scaling_factor'] = 0.5  # 小气泡内压力缩放因子
    params['vacancy_contribution_weight'] = 1.2  # 空位贡献项权重
    
    # 增加最大步数，以便能够模拟足够长的物理时间
    max_steps = 1000000  # 100万步
    
    print(f"测试4参数设置:")
    print(f"- 温度: {params['temperature']}K")
    print(f"- 表面能: {params['surface_energy']}J/m^2")
    print(f"- 临界半径: {params['critical_radius']*1e9} nm")
    print(f"- 半径演化平滑因子: {params['radius_smoothing_factor']}")
    print(f"- 小气泡内压力缩放因子: {params['pressure_scaling_factor']}")
    print(f"- 空位贡献项权重: {params['vacancy_contribution_weight']}")
    print(f"- 最大计算步数: {max_steps}步")
    print(f"- 模拟时间: {sim_time}秒 (6分钟)")
    print(f"- 优化目标: 改进气泡半径演化逻辑，特别是小气泡的处理")
    
    logger.info("开始执行测试4（优化气泡半径演化逻辑）")
    # 运行测试4
    result, swelling = run_test4(
        sim_time=sim_time,
        dt=params['time_step'],
        max_dt=params['max_time_step'],
        max_steps=max_steps,
        output_interval=1000,  # 每1000步输出一次详细状态
        save_path='test4_results_euler.png',
        debug_plots_dir='test4_debug_euler_plots/'
    )
    
    # 分析测试结果
    if result is not None:
        analyze_test_results()  # 比较测试3和测试4的结果
    
    print("测试4完成")
    logger.info("======== 程序正常结束 ========")


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
铀合金肿胀行为综合研究脚本
用于系统研究不同温度和辐照条件下的肿胀行为，特别是高燃耗条件下的预测

作者: 研究团队
日期: 2025年6月
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# 导入我们优化后的模型
from models.euler_model_v5 import EnhancedEulerGasSwellingModel
from params.parameters import create_default_parameters

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('uranium_swelling_study.log'),
        logging.StreamHandler()
    ]
)

class UraniumSwellingStudy:
    """铀合金肿胀行为研究类"""
    
    def __init__(self, output_dir: str = "swelling_study_results"):
        """
        初始化研究类
        
        Args:
            output_dir: 结果输出目录
        """
        self.output_dir = output_dir
        self.create_output_directories()
        self.results = {}
        
    def create_output_directories(self):
        """创建输出目录结构"""
        dirs = [
            self.output_dir,
            f"{self.output_dir}/temperature_study",
            f"{self.output_dir}/burnup_study", 
            f"{self.output_dir}/parametric_study",
            f"{self.output_dir}/data",
            f"{self.output_dir}/plots"
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
            
    def temperature_parametric_study(self, 
                                   temperatures: Optional[List[float]] = None,
                                   simulation_time: float = 3600 * 24 * 30,  # 30天
                                   max_steps: int = 100000) -> Dict:
        """
        温度参数研究
        
        Args:
            temperatures: 温度列表 (K)
            simulation_time: 模拟时间 (s)
            max_steps: 最大步数
            
        Returns:
            研究结果字典
        """
        if temperatures is None:
            # 覆盖典型的反应堆运行温度范围
            temperatures = [573, 623, 673, 723, 773, 823, 873, 923, 973]  # 300-700°C
            
        logging.info(f"开始温度参数研究，温度范围: {min(temperatures)}-{max(temperatures)} K")
        
        results = {
            'temperatures': temperatures,
            'swelling_rates': [],
            'final_swelling': [],
            'bubble_densities': [],
            'average_bubble_radius': [],
            'gas_release_fractions': [],
            'simulation_data': []
        }
        
        for temp in temperatures:
            logging.info(f"计算温度 {temp} K...")
            
            # 创建参数
            params = create_default_parameters()
            params['temperature'] = temp
            
            # 根据温度调整一些参数
            if temp > 873:  # 高温条件
                params['surface_energy'] = 0.6  # 高温下表面能降低
                params['resolution_rate'] *= 2  # 高温下重溶率增加
            
            # 创建并运行模型
            model = EnhancedEulerGasSwellingModel(params)
            
            try:
                result = model.euler_solve(
                    t_span=(0, simulation_time),
                    max_steps=max_steps
                )
                
                if result['success']:
                    # 计算关键指标
                    swelling = result['swelling_percent'][-1]
                    swelling_rate = swelling / (simulation_time / (3600 * 24))  # %/day
                    
                    # 气泡密度 (基体 + 界面)
                    bubble_density = result['Ccb'][-1] + result['Ccf'][-1]
                    
                    # 平均气泡半径
                    avg_radius = (result['Rcb'][-1] + result['Rcf'][-1]) / 2
                    
                    # 气体释放分数
                    total_gas_generated = params['gas_production_rate'] * params['fission_rate'] * simulation_time
                    gas_release_fraction = result['released_gas'][-1] / total_gas_generated if total_gas_generated > 0 else 0
                    
                    results['swelling_rates'].append(swelling_rate)
                    results['final_swelling'].append(swelling)
                    results['bubble_densities'].append(bubble_density)
                    results['average_bubble_radius'].append(avg_radius)
                    results['gas_release_fractions'].append(gas_release_fraction)
                    results['simulation_data'].append(result)
                    
                    logging.info(f"温度 {temp} K: 肿胀率 {swelling:.3f}%, 肿胀速率 {swelling_rate:.6f} %/day")
                    
                else:
                    logging.warning(f"温度 {temp} K 计算失败")
                    # 添加空值
                    for key in ['swelling_rates', 'final_swelling', 'bubble_densities', 
                               'average_bubble_radius', 'gas_release_fractions']:
                        results[key].append(np.nan)
                    results['simulation_data'].append(None)
                    
            except Exception as e:
                logging.error(f"温度 {temp} K 计算出错: {str(e)}")
                # 添加空值
                for key in ['swelling_rates', 'final_swelling', 'bubble_densities', 
                           'average_bubble_radius', 'gas_release_fractions']:
                    results[key].append(np.nan)
                results['simulation_data'].append(None)
        
        self.results['temperature_study'] = results
        return results
    
    def burnup_parametric_study(self,
                              burnup_levels: Optional[List[float]] = None,
                              temperature: float = 773,  # 500°C
                              max_steps: int = 200000) -> Dict:
        """
        燃耗参数研究 - 重点关注高燃耗条件
        
        Args:
            burnup_levels: 燃耗水平列表 (GWd/tU)
            temperature: 温度 (K)
            max_steps: 最大步数
            
        Returns:
            研究结果字典
        """
        if burnup_levels is None:
            # 从低燃耗到高燃耗，包括超高燃耗
            burnup_levels = [1, 5, 10, 20, 30, 50, 70, 100, 150, 200]  # GWd/tU
            
        logging.info(f"开始燃耗参数研究，燃耗范围: {min(burnup_levels)}-{max(burnup_levels)} GWd/tU")
        
        results = {
            'burnup_levels': burnup_levels,
            'swelling_evolution': [],
            'bubble_evolution': [],
            'gas_release_evolution': [],
            'simulation_times': [],
            'simulation_data': []
        }
        
        for burnup in burnup_levels:
            logging.info(f"计算燃耗 {burnup} GWd/tU...")
            
            # 根据燃耗计算模拟时间
            # 假设功率密度为 40 MW/tU
            power_density = 40e6  # W/tU
            simulation_time = burnup * 1e9 * 24 * 3600 / power_density  # 秒
            
            # 创建参数
            params = create_default_parameters()
            params['temperature'] = temperature
            
            # 根据燃耗调整参数
            if burnup > 50:  # 高燃耗条件
                # 高燃耗下位错密度增加
                params['dislocation_density'] *= (1 + burnup/100)
                # 高燃耗下气体生成率可能变化
                params['gas_production_rate'] *= (1 + burnup/200)
                # 高燃耗下重溶率可能降低
                params['resolution_rate'] *= (1 - burnup/500)
            
            # 创建并运行模型
            model = EnhancedEulerGasSwellingModel(params)
            
            try:
                result = model.euler_solve(
                    t_span=(0, simulation_time),
                    max_steps=max_steps
                )
                
                if result['success']:
                    results['swelling_evolution'].append(result['swelling_percent'])
                    results['bubble_evolution'].append({
                        'Ccb': result['Ccb'],
                        'Ccf': result['Ccf'],
                        'Rcb': result['Rcb'],
                        'Rcf': result['Rcf']
                    })
                    results['gas_release_evolution'].append(result['released_gas'])
                    results['simulation_times'].append(result['time'])
                    results['simulation_data'].append(result)
                    
                    final_swelling = result['swelling_percent'][-1]
                    logging.info(f"燃耗 {burnup} GWd/tU: 最终肿胀率 {final_swelling:.3f}%")
                    
                else:
                    logging.warning(f"燃耗 {burnup} GWd/tU 计算失败")
                    # 添加空值
                    results['swelling_evolution'].append([])
                    results['bubble_evolution'].append({})
                    results['gas_release_evolution'].append([])
                    results['simulation_times'].append([])
                    results['simulation_data'].append(None)
                    
            except Exception as e:
                logging.error(f"燃耗 {burnup} GWd/tU 计算出错: {str(e)}")
                # 添加空值
                results['swelling_evolution'].append([])
                results['bubble_evolution'].append({})
                results['gas_release_evolution'].append([])
                results['simulation_times'].append([])
                results['simulation_data'].append(None)
        
        self.results['burnup_study'] = results
        return results
    
    def high_burnup_detailed_study(self,
                                 burnup: float = 150,  # GWd/tU
                                 temperatures: Optional[List[float]] = None,
                                 max_steps: int = 300000) -> Dict:
        """
        高燃耗条件下的详细研究
        
        Args:
            burnup: 燃耗水平 (GWd/tU)
            temperatures: 温度列表 (K)
            max_steps: 最大步数
            
        Returns:
            研究结果字典
        """
        if temperatures is None:
            temperatures = [673, 723, 773, 823, 873]  # 400-600°C
            
        logging.info(f"开始高燃耗({burnup} GWd/tU)详细研究")
        
        # 计算模拟时间
        power_density = 40e6  # W/tU
        simulation_time = burnup * 1e9 * 24 * 3600 / power_density
        
        results = {
            'burnup': burnup,
            'temperatures': temperatures,
            'simulation_time': simulation_time,
            'detailed_results': {}
        }
        
        for temp in temperatures:
            logging.info(f"高燃耗条件下计算温度 {temp} K...")
            
            # 创建高燃耗参数
            params = create_default_parameters()
            params['temperature'] = temp
            
            # 高燃耗条件下的参数调整
            params['dislocation_density'] *= (1 + burnup/100)
            params['gas_production_rate'] *= (1 + burnup/200)
            params['resolution_rate'] *= max(0.1, 1 - burnup/500)  # 最小保持10%
            
            # 高温高燃耗下的额外调整
            if temp > 823:
                params['surface_energy'] *= 0.8  # 表面能降低
                params['Fnb'] *= 2  # 成核因子增加
                params['Fnf'] *= 2
            
            # 创建并运行模型
            model = EnhancedEulerGasSwellingModel(params)
            
            try:
                result = model.euler_solve(
                    t_span=(0, simulation_time),
                    max_steps=max_steps
                )
                
                if result['success']:
                    # 详细分析结果
                    analysis = self.analyze_detailed_results(result, params)
                    results['detailed_results'][temp] = {
                        'simulation_result': result,
                        'analysis': analysis,
                        'parameters': params
                    }
                    
                    logging.info(f"高燃耗温度 {temp} K: 最终肿胀率 {analysis['final_swelling']:.3f}%")
                    
                else:
                    logging.warning(f"高燃耗温度 {temp} K 计算失败")
                    results['detailed_results'][temp] = None
                    
            except Exception as e:
                logging.error(f"高燃耗温度 {temp} K 计算出错: {str(e)}")
                results['detailed_results'][temp] = None
        
        self.results['high_burnup_study'] = results
        return results
    
    def analyze_detailed_results(self, result: Dict, params: Dict) -> Dict:
        """
        详细分析模拟结果
        
        Args:
            result: 模拟结果
            params: 模拟参数
            
        Returns:
            分析结果字典
        """
        analysis = {}
        
        # 基本指标
        analysis['final_swelling'] = result['swelling_percent'][-1]
        analysis['max_swelling_rate'] = np.max(np.gradient(result['swelling_percent']))
        
        # 气泡特征
        analysis['final_bubble_density_bulk'] = result['Ccb'][-1]
        analysis['final_bubble_density_interface'] = result['Ccf'][-1]
        analysis['final_bubble_radius_bulk'] = result['Rcb'][-1]
        analysis['final_bubble_radius_interface'] = result['Rcf'][-1]
        
        # 气体分布
        total_gas = result['Cgb'][-1] + result['Cgf'][-1] + \
                   result['Ccb'][-1] * result['Ncb'][-1] + \
                   result['Ccf'][-1] * result['Ncf'][-1] + \
                   result['released_gas'][-1]
        
        if total_gas > 0:
            analysis['gas_in_solution_fraction'] = (result['Cgb'][-1] + result['Cgf'][-1]) / total_gas
            analysis['gas_in_bubbles_fraction'] = (result['Ccb'][-1] * result['Ncb'][-1] + 
                                                 result['Ccf'][-1] * result['Ncf'][-1]) / total_gas
            analysis['gas_release_fraction'] = result['released_gas'][-1] / total_gas
        else:
            analysis['gas_in_solution_fraction'] = 0
            analysis['gas_in_bubbles_fraction'] = 0
            analysis['gas_release_fraction'] = 0
        
        # 时间特征
        # 找到肿胀率达到1%的时间
        swelling_1_percent_idx = np.where(np.array(result['swelling_percent']) >= 1.0)[0]
        if len(swelling_1_percent_idx) > 0:
            analysis['time_to_1_percent_swelling'] = result['time'][swelling_1_percent_idx[0]]
        else:
            analysis['time_to_1_percent_swelling'] = None
            
        return analysis
    
    def plot_temperature_study_results(self):
        """绘制温度研究结果"""
        if 'temperature_study' not in self.results:
            logging.warning("没有温度研究结果可绘制")
            return
            
        results = self.results['temperature_study']
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('温度对铀合金肿胀行为的影响', fontsize=16, fontweight='bold')
        
        # 1. 最终肿胀率 vs 温度
        axes[0,0].plot(results['temperatures'], results['final_swelling'], 'bo-', linewidth=2, markersize=8)
        axes[0,0].set_xlabel('温度 (K)')
        axes[0,0].set_ylabel('最终肿胀率 (%)')
        axes[0,0].set_title('最终肿胀率随温度变化')
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. 肿胀速率 vs 温度
        axes[0,1].plot(results['temperatures'], results['swelling_rates'], 'ro-', linewidth=2, markersize=8)
        axes[0,1].set_xlabel('温度 (K)')
        axes[0,1].set_ylabel('肿胀速率 (%/day)')
        axes[0,1].set_title('肿胀速率随温度变化')
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. 气泡密度 vs 温度
        axes[0,2].semilogy(results['temperatures'], results['bubble_densities'], 'go-', linewidth=2, markersize=8)
        axes[0,2].set_xlabel('温度 (K)')
        axes[0,2].set_ylabel('气泡密度 (m⁻³)')
        axes[0,2].set_title('气泡密度随温度变化')
        axes[0,2].grid(True, alpha=0.3)
        
        # 4. 平均气泡半径 vs 温度
        axes[1,0].plot(results['temperatures'], np.array(results['average_bubble_radius'])*1e9, 'mo-', linewidth=2, markersize=8)
        axes[1,0].set_xlabel('温度 (K)')
        axes[1,0].set_ylabel('平均气泡半径 (nm)')
        axes[1,0].set_title('平均气泡半径随温度变化')
        axes[1,0].grid(True, alpha=0.3)
        
        # 5. 气体释放分数 vs 温度
        axes[1,1].plot(results['temperatures'], results['gas_release_fractions'], 'co-', linewidth=2, markersize=8)
        axes[1,1].set_xlabel('温度 (K)')
        axes[1,1].set_ylabel('气体释放分数')
        axes[1,1].set_title('气体释放分数随温度变化')
        axes[1,1].grid(True, alpha=0.3)
        
        # 6. Arrhenius图 (ln(肿胀速率) vs 1/T)
        valid_indices = ~np.isnan(results['swelling_rates'])
        if np.any(valid_indices):
            temps_valid = np.array(results['temperatures'])[valid_indices]
            rates_valid = np.array(results['swelling_rates'])[valid_indices]
            rates_valid = rates_valid[rates_valid > 0]  # 只取正值
            temps_valid = temps_valid[:len(rates_valid)]
            
            if len(rates_valid) > 0:
                axes[1,2].semilogy(1000/temps_valid, rates_valid, 'ko-', linewidth=2, markersize=8)
                axes[1,2].set_xlabel('1000/T (K⁻¹)')
                axes[1,2].set_ylabel('肿胀速率 (%/day)')
                axes[1,2].set_title('Arrhenius图')
                axes[1,2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/temperature_study_summary.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_burnup_study_results(self):
        """绘制燃耗研究结果"""
        if 'burnup_study' not in self.results:
            logging.warning("没有燃耗研究结果可绘制")
            return
            
        results = self.results['burnup_study']
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('燃耗对铀合金肿胀行为的影响', fontsize=16, fontweight='bold')
        
        # 1. 肿胀演化随燃耗变化
        for i, burnup in enumerate(results['burnup_levels']):
            if len(results['swelling_evolution'][i]) > 0:
                time_days = np.array(results['simulation_times'][i]) / (24 * 3600)
                axes[0,0].plot(time_days, results['swelling_evolution'][i], 
                              label=f'{burnup} GWd/tU', linewidth=2)
        
        axes[0,0].set_xlabel('时间 (天)')
        axes[0,0].set_ylabel('肿胀率 (%)')
        axes[0,0].set_title('肿胀演化随燃耗变化')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. 最终肿胀率 vs 燃耗
        final_swellings = []
        for swelling_data in results['swelling_evolution']:
            if len(swelling_data) > 0:
                final_swellings.append(swelling_data[-1])
            else:
                final_swellings.append(np.nan)
        
        axes[0,1].plot(results['burnup_levels'], final_swellings, 'bo-', linewidth=2, markersize=8)
        axes[0,1].set_xlabel('燃耗 (GWd/tU)')
        axes[0,1].set_ylabel('最终肿胀率 (%)')
        axes[0,1].set_title('最终肿胀率随燃耗变化')
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. 气泡半径演化
        for i, burnup in enumerate(results['burnup_levels']):
            if 'Rcb' in results['bubble_evolution'][i]:
                time_days = np.array(results['simulation_times'][i]) / (24 * 3600)
                radius_nm = np.array(results['bubble_evolution'][i]['Rcb']) * 1e9
                axes[1,0].plot(time_days, radius_nm, 
                              label=f'{burnup} GWd/tU', linewidth=2)
        
        axes[1,0].set_xlabel('时间 (天)')
        axes[1,0].set_ylabel('基体气泡半径 (nm)')
        axes[1,0].set_title('气泡半径演化随燃耗变化')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. 气体释放演化
        for i, burnup in enumerate(results['burnup_levels']):
            if len(results['gas_release_evolution'][i]) > 0:
                time_days = np.array(results['simulation_times'][i]) / (24 * 3600)
                axes[1,1].plot(time_days, results['gas_release_evolution'][i], 
                              label=f'{burnup} GWd/tU', linewidth=2)
        
        axes[1,1].set_xlabel('时间 (天)')
        axes[1,1].set_ylabel('累积气体释放 (atoms/m³)')
        axes[1,1].set_title('气体释放演化随燃耗变化')
        axes[1,1].legend()
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/burnup_study_summary.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_high_burnup_study_results(self):
        """绘制高燃耗研究结果"""
        if 'high_burnup_study' not in self.results:
            logging.warning("没有高燃耗研究结果可绘制")
            return
            
        results = self.results['high_burnup_study']
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'高燃耗条件({results["burnup"]} GWd/tU)下的详细分析', fontsize=16, fontweight='bold')
        
        temperatures = []
        final_swellings = []
        bubble_densities = []
        gas_release_fractions = []
        
        # 收集数据
        for temp in results['temperatures']:
            if temp in results['detailed_results'] and results['detailed_results'][temp] is not None:
                analysis = results['detailed_results'][temp]['analysis']
                temperatures.append(temp)
                final_swellings.append(analysis['final_swelling'])
                bubble_densities.append(analysis['final_bubble_density_bulk'] + analysis['final_bubble_density_interface'])
                gas_release_fractions.append(analysis['gas_release_fraction'])
        
        # 1. 最终肿胀率 vs 温度
        if temperatures:
            axes[0,0].plot(temperatures, final_swellings, 'bo-', linewidth=2, markersize=8)
            axes[0,0].set_xlabel('温度 (K)')
            axes[0,0].set_ylabel('最终肿胀率 (%)')
            axes[0,0].set_title('高燃耗下最终肿胀率随温度变化')
            axes[0,0].grid(True, alpha=0.3)
        
        # 2. 肿胀演化对比
        for temp in results['temperatures']:
            if temp in results['detailed_results'] and results['detailed_results'][temp] is not None:
                result = results['detailed_results'][temp]['simulation_result']
                time_days = np.array(result['time']) / (24 * 3600)
                axes[0,1].plot(time_days, result['swelling_percent'], 
                              label=f'{temp} K', linewidth=2)
        
        axes[0,1].set_xlabel('时间 (天)')
        axes[0,1].set_ylabel('肿胀率 (%)')
        axes[0,1].set_title('高燃耗下肿胀演化')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # 3. 气泡密度 vs 温度
        if temperatures:
            axes[0,2].semilogy(temperatures, bubble_densities, 'go-', linewidth=2, markersize=8)
            axes[0,2].set_xlabel('温度 (K)')
            axes[0,2].set_ylabel('总气泡密度 (m⁻³)')
            axes[0,2].set_title('高燃耗下气泡密度随温度变化')
            axes[0,2].grid(True, alpha=0.3)
        
        # 4. 气体分布饼图 (选择中等温度)
        if len(results['temperatures']) >= 3:
            mid_temp = results['temperatures'][len(results['temperatures'])//2]
            if mid_temp in results['detailed_results'] and results['detailed_results'][mid_temp] is not None:
                analysis = results['detailed_results'][mid_temp]['analysis']
                
                labels = ['溶解态', '气泡内', '已释放']
                sizes = [analysis['gas_in_solution_fraction'], 
                        analysis['gas_in_bubbles_fraction'],
                        analysis['gas_release_fraction']]
                
                axes[1,0].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                axes[1,0].set_title(f'气体分布 ({mid_temp} K)')
        
        # 5. 气体释放分数 vs 温度
        if temperatures:
            axes[1,1].plot(temperatures, gas_release_fractions, 'ro-', linewidth=2, markersize=8)
            axes[1,1].set_xlabel('温度 (K)')
            axes[1,1].set_ylabel('气体释放分数')
            axes[1,1].set_title('高燃耗下气体释放分数随温度变化')
            axes[1,1].grid(True, alpha=0.3)
        
        # 6. 气泡半径对比
        for temp in results['temperatures']:
            if temp in results['detailed_results'] and results['detailed_results'][temp] is not None:
                result = results['detailed_results'][temp]['simulation_result']
                time_days = np.array(result['time']) / (24 * 3600)
                radius_nm = np.array(result['Rcb']) * 1e9
                axes[1,2].plot(time_days, radius_nm, 
                              label=f'{temp} K', linewidth=2)
        
        axes[1,2].set_xlabel('时间 (天)')
        axes[1,2].set_ylabel('基体气泡半径 (nm)')
        axes[1,2].set_title('高燃耗下气泡半径演化')
        axes[1,2].legend()
        axes[1,2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/plots/high_burnup_study_summary.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_results_to_excel(self):
        """将结果保存到Excel文件"""
        with pd.ExcelWriter(f'{self.output_dir}/data/uranium_swelling_study_results.xlsx') as writer:
            
            # 温度研究结果
            if 'temperature_study' in self.results:
                temp_data = self.results['temperature_study']
                temp_df = pd.DataFrame({
                    'Temperature_K': temp_data['temperatures'],
                    'Final_Swelling_Percent': temp_data['final_swelling'],
                    'Swelling_Rate_Percent_per_Day': temp_data['swelling_rates'],
                    'Bubble_Density_per_m3': temp_data['bubble_densities'],
                    'Average_Bubble_Radius_m': temp_data['average_bubble_radius'],
                    'Gas_Release_Fraction': temp_data['gas_release_fractions']
                })
                temp_df.to_excel(writer, sheet_name='Temperature_Study', index=False)
            
            # 燃耗研究结果
            if 'burnup_study' in self.results:
                burnup_data = self.results['burnup_study']
                final_swellings = []
                for swelling_data in burnup_data['swelling_evolution']:
                    if len(swelling_data) > 0:
                        final_swellings.append(swelling_data[-1])
                    else:
                        final_swellings.append(np.nan)
                
                burnup_df = pd.DataFrame({
                    'Burnup_GWd_per_tU': burnup_data['burnup_levels'],
                    'Final_Swelling_Percent': final_swellings
                })
                burnup_df.to_excel(writer, sheet_name='Burnup_Study', index=False)
            
            # 高燃耗详细研究结果
            if 'high_burnup_study' in self.results:
                hb_data = self.results['high_burnup_study']
                hb_results = []
                
                for temp in hb_data['temperatures']:
                    if temp in hb_data['detailed_results'] and hb_data['detailed_results'][temp] is not None:
                        analysis = hb_data['detailed_results'][temp]['analysis']
                        hb_results.append({
                            'Temperature_K': temp,
                            'Final_Swelling_Percent': analysis['final_swelling'],
                            'Max_Swelling_Rate': analysis['max_swelling_rate'],
                            'Final_Bubble_Density_Bulk': analysis['final_bubble_density_bulk'],
                            'Final_Bubble_Density_Interface': analysis['final_bubble_density_interface'],
                            'Gas_in_Solution_Fraction': analysis['gas_in_solution_fraction'],
                            'Gas_in_Bubbles_Fraction': analysis['gas_in_bubbles_fraction'],
                            'Gas_Release_Fraction': analysis['gas_release_fraction'],
                            'Time_to_1_Percent_Swelling_s': analysis['time_to_1_percent_swelling']
                        })
                
                if hb_results:
                    hb_df = pd.DataFrame(hb_results)
                    hb_df.to_excel(writer, sheet_name='High_Burnup_Study', index=False)
        
        logging.info(f"结果已保存到 {self.output_dir}/data/uranium_swelling_study_results.xlsx")
    
    def save_results_to_json(self):
        """将结果保存到JSON文件"""
        # 创建可序列化的结果副本
        serializable_results = {}
        
        for study_name, study_data in self.results.items():
            serializable_results[study_name] = {}
            
            for key, value in study_data.items():
                if isinstance(value, np.ndarray):
                    serializable_results[study_name][key] = value.tolist()
                elif isinstance(value, list):
                    # 处理包含numpy数组的列表
                    new_list = []
                    for item in value:
                        if isinstance(item, np.ndarray):
                            new_list.append(item.tolist())
                        elif isinstance(item, dict):
                            new_dict = {}
                            for k, v in item.items():
                                if isinstance(v, np.ndarray):
                                    new_dict[k] = v.tolist()
                                else:
                                    new_dict[k] = v
                            new_list.append(new_dict)
                        else:
                            new_list.append(item)
                    serializable_results[study_name][key] = new_list
                else:
                    serializable_results[study_name][key] = value
        
        with open(f'{self.output_dir}/data/uranium_swelling_study_results.json', 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logging.info(f"结果已保存到 {self.output_dir}/data/uranium_swelling_study_results.json")
    
    def generate_summary_report(self):
        """生成总结报告"""
        report_path = f'{self.output_dir}/uranium_swelling_study_report.md'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 铀合金肿胀行为综合研究报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 研究概述\n\n")
            f.write("本研究使用优化后的辐射气体气泡肿胀模型，系统地研究了不同温度和辐照条件下的铀合金肿胀行为，")
            f.write("特别关注了高燃耗条件下的预测。\n\n")
            
            # 温度研究总结
            if 'temperature_study' in self.results:
                f.write("## 温度影响研究\n\n")
                temp_data = self.results['temperature_study']
                f.write(f"- 研究温度范围: {min(temp_data['temperatures'])}-{max(temp_data['temperatures'])} K\n")
                
                valid_swellings = [s for s in temp_data['final_swelling'] if not np.isnan(s)]
                if valid_swellings:
                    f.write(f"- 最终肿胀率范围: {min(valid_swellings):.3f}-{max(valid_swellings):.3f}%\n")
                
                valid_rates = [r for r in temp_data['swelling_rates'] if not np.isnan(r)]
                if valid_rates:
                    f.write(f"- 肿胀速率范围: {min(valid_rates):.6f}-{max(valid_rates):.6f} %/day\n\n")
            
            # 燃耗研究总结
            if 'burnup_study' in self.results:
                f.write("## 燃耗影响研究\n\n")
                burnup_data = self.results['burnup_study']
                f.write(f"- 研究燃耗范围: {min(burnup_data['burnup_levels'])}-{max(burnup_data['burnup_levels'])} GWd/tU\n")
                
                final_swellings = []
                for swelling_data in burnup_data['swelling_evolution']:
                    if len(swelling_data) > 0:
                        final_swellings.append(swelling_data[-1])
                
                if final_swellings:
                    f.write(f"- 最终肿胀率范围: {min(final_swellings):.3f}-{max(final_swellings):.3f}%\n\n")
            
            # 高燃耗研究总结
            if 'high_burnup_study' in self.results:
                f.write("## 高燃耗条件详细研究\n\n")
                hb_data = self.results['high_burnup_study']
                f.write(f"- 燃耗水平: {hb_data['burnup']} GWd/tU\n")
                f.write(f"- 研究温度范围: {min(hb_data['temperatures'])}-{max(hb_data['temperatures'])} K\n")
                
                # 统计有效结果
                valid_results = 0
                for temp in hb_data['temperatures']:
                    if temp in hb_data['detailed_results'] and hb_data['detailed_results'][temp] is not None:
                        valid_results += 1
                
                f.write(f"- 成功计算的温度点: {valid_results}/{len(hb_data['temperatures'])}\n\n")
            
            f.write("## 主要发现\n\n")
            f.write("1. 温度对肿胀行为有显著影响，高温下肿胀率和肿胀速率都显著增加\n")
            f.write("2. 燃耗水平是影响肿胀的关键因素，高燃耗条件下肿胀行为更加复杂\n")
            f.write("3. 气泡的形成、生长和聚集过程在不同条件下表现出不同的特征\n")
            f.write("4. 气体释放机制在高温高燃耗条件下变得更加重要\n\n")
            
            f.write("## 文件说明\n\n")
            f.write("- `plots/`: 包含所有研究结果的图表\n")
            f.write("- `data/`: 包含Excel和JSON格式的数值结果\n")
            f.write("- `uranium_swelling_study.log`: 详细的计算日志\n\n")
        
        logging.info(f"总结报告已生成: {report_path}")

def main():
    """主函数"""
    print("=" * 60)
    print("铀合金肿胀行为综合研究")
    print("=" * 60)
    
    # 创建研究实例
    study = UraniumSwellingStudy()
    
    try:
        # 1. 温度参数研究
        print("\n1. 开始温度参数研究...")
        study.temperature_parametric_study()
        study.plot_temperature_study_results()
        
        # 2. 燃耗参数研究
        print("\n2. 开始燃耗参数研究...")
        study.burnup_parametric_study()
        study.plot_burnup_study_results()
        
        # 3. 高燃耗详细研究
        print("\n3. 开始高燃耗详细研究...")
        study.high_burnup_detailed_study()
        study.plot_high_burnup_study_results()
        
        # 4. 保存结果
        print("\n4. 保存研究结果...")
        study.save_results_to_excel()
        study.save_results_to_json()
        study.generate_summary_report()
        
        print(f"\n研究完成！结果保存在 {study.output_dir} 目录中")
        
    except Exception as e:
        logging.error(f"研究过程中出现错误: {str(e)}")
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()



import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='temperature_sweep.log',
    filemode='w'
)
logger = logging.getLogger('temperature_sweep')

def run_temperature_sweep():
    """在不同温度下运行肿胀模型并收集结果"""
    temperatures = np.arange(300, 1001, 50)  # 400K到1000K，每50K一个点
    swelling_results = []
    
    logger.info(f"开始温度扫描: {temperatures}K")
    
    for temp in temperatures:
        logger.info(f"===== 开始运行温度: {temp}K =====")
        
        try:
            # 创建参数
            params = create_default_parameters()
            
            # 设置当前温度
            params['temperature'] = temp
            
            # 使用优化后的参数设置
            params['time_step'] = 1e-9
            params['max_time_step'] = 0.1
            params['Fnb'] = 1e-5
            params['Fnf'] = 1e-5
            params['dislocation_density'] = 7.0e13
            params['surface_energy'] = 0.5
            params['resolution_rate'] = 2.0e-5
            params['Dgb_prefactor'] = 8.55e-12
            params['Dgb_fission_term'] = 1.0e-40
            params['Dgf_multiplier'] = 1e0
            params['Dv0'] = 7.767e-10
            params['Di0'] = 1.259e-8
            params['Evm'] = 0.347
            params['Eim'] = 0.42
            params['Evfmuti'] = 1.0
            params['fission_rate'] = 5e19
            params['gas_production_rate'] = 0.5
            params['critical_radius'] = 50e-9
            params['radius_smoothing_factor'] = 0.8
            params['pressure_scaling_factor'] = 0.5
            params['vacancy_contribution_weight'] = 1.2
            
            # 创建模型
            model = GasSwellingModel(params)
            model.initial_state[2] = 4.0  # Ncb
            model.initial_state[6] = 4.0  # Ncf
            
            # 运行模拟
            sim_time = 4176980  # 2小时
            t_eval = np.linspace(0, sim_time, 100)
            result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
            
            # 计算肿胀率
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']
            
            V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100  # 肿胀率（百分比）
            
            final_swelling = swelling[-1]
            swelling_results.append((temp, final_swelling))
            
            logger.info(f"温度 {temp}K 完成 - 最终肿胀率: {final_swelling:.6f}%")
            
        except Exception as e:
            logger.error(f"温度 {temp}K 运行失败: {str(e)}")
            swelling_results.append((temp, None))
    
    return swelling_results

def plot_swelling_vs_temperature(results, save_path='swelling_vs_temperature.png'):
    """绘制肿胀率随温度变化的图表"""
    temperatures = [r[0] for r in results]
    swellings = [r[1] for r in results if r[1] is not None]
    valid_temps = [r[0] for r in results if r[1] is not None]
    
    plt.figure(figsize=(10, 6))
    plt.plot(valid_temps, swellings, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Temperature (K)')
    plt.ylabel('Swelling (%)')
    plt.title('Swellng vs Temperture')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    logger.info(f"肿胀率-温度图表已保存至: {save_path}")

def save_results_to_csv(results, filename='swelling_results.csv'):
    """将结果保存到CSV文件"""
    with open(filename, 'w') as f:
        f.write("Temperature(K),Swelling(%)\n")
        for temp, swelling in results:
            if swelling is not None:
                f.write(f"{temp},{swelling:.6f}\n")
            else:
                f.write(f"{temp},NaN\n")
    logger.info(f"结果已保存至CSV文件: {filename}")

if __name__ == "__main__":
    logger.info("======== 开始温度扫描程序 ========")
    results = run_temperature_sweep()
    
    # 打印结果
    print("\n温度扫描结果:")
    print("温度(K)\t肿胀率(%)")
    for temp, swelling in results:
        if swelling is not None:
            print(f"{temp}\t{swelling:.6f}")
        else:
            print(f"{temp}\t运行失败")
    
    # 保存和绘图
    save_results_to_csv(results)
    plot_swelling_vs_temperature(results)
    
    logger.info("======== 温度扫描程序完成 ========")


# -*- coding: utf-8 -*-
"""
Created on Wed Oct 29 09:34:24 2025

@author: kongxiangzhe
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='temperature_sweep.log',
    filemode='w'
)
logger = logging.getLogger('temperature_sweep')

def run_temperature_sweep():
    """在不同温度下运行肿胀模型并收集结果"""
    temperatures = np.arange(300, 1001, 50)  # 400K到1000K，每50K一个点
    base_dislocation_density = 7.0e13
    dislocation_multipliers = [10, 2, 1, 0.5, 0.1]  # 位错密度倍数
    results = {mult: [] for mult in dislocation_multipliers}  # 存储不同位错密度的结果
    
    logger.info(f"开始温度扫描: {temperatures}K")
    logger.info(f"位错密度倍数: {dislocation_multipliers}")
    
    for temp in temperatures:
        logger.info(f"===== 开始运行温度: {temp}K =====")
        
        for multiplier in dislocation_multipliers:
            dislocation_density = base_dislocation_density * multiplier
            logger.info(f"位错密度倍数: {multiplier}x ({dislocation_density:.1e})")
            
            try:
                # 创建参数
                params = create_default_parameters()
                
                # 设置当前温度和位错密度
                params['temperature'] = temp
                params['dislocation_density'] = dislocation_density
                
                # 使用优化后的参数设置
                params['time_step'] = 1e-9
                params['max_time_step'] = 0.1
                params['Fnb'] = 1e-5
                params['Fnf'] = 1e-5
                params['surface_energy'] = 0.5
                params['resolution_rate'] = 2.0e-5
                params['Dgb_prefactor'] = 8.55e-12
                params['Dgb_fission_term'] = 1.0e-40
                params['Dgf_multiplier'] = 1e0
                params['Dv0'] = 7.767e-11
                params['Di0'] = 1.259e-6
                params['Evm'] = 0.434
                params['Eim'] = 0.42
                params['Evfmuti'] = 1.0
                params['fission_rate'] = 5e19
                params['gas_production_rate'] = 0.55
                params['critical_radius'] = 50e-9
                params['radius_smoothing_factor'] = 0.8
                params['pressure_scaling_factor'] = 0.5
                params['vacancy_contribution_weight'] = 1.2
                
                # 创建模型
                model = GasSwellingModel(params)
                model.initial_state[2] = 4.0  # Ncb
                model.initial_state[6] = 4.0  # Ncf
                
                # 运行模拟
                sim_time = 4176980  # 2小时
                t_eval = np.linspace(0, sim_time, 100)
                result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
                
                # 计算肿胀率
                Rcb = result['Rcb']
                Rcf = result['Rcf']
                Ccb = result['Ccb']
                Ccf = result['Ccf']
                
                V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
                V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
                total_V_bubble = V_bubble_b + V_bubble_f
                swelling = total_V_bubble * 100  # 肿胀率（百分比）
                
                final_swelling = swelling[-1]
                results[multiplier].append((temp, final_swelling))
                
                logger.info(f"温度 {temp}K | 位错密度倍数 {multiplier}x - 最终肿胀率: {final_swelling:.6f}%")
                
            except Exception as e:
                logger.error(f"温度 {temp}K | 位错密度倍数 {multiplier}x 运行失败: {str(e)}")
                results[multiplier].append((temp, None))
    
    return results

def plot_swelling_vs_temperature(results, save_path='swelling_vs_temperature.png'):
    """绘制肿胀率随温度变化的图表"""
    plt.figure(figsize=(12, 8))
    
    # 不同位错密度的颜色和标记
    markers = ['o', 's', 'D', '^', 'v']
    colors = ['b', 'g', 'r', 'c', 'm']
    
    for i, (multiplier, data) in enumerate(results.items()):
        temperatures = [d[0] for d in data]
        swellings = [d[1] for d in data if d[1] is not None]
        valid_temps = [d[0] for d in data if d[1] is not None]
        
        # 绘制曲线
        plt.plot(
            valid_temps, swellings, 
            marker=markers[i], color=colors[i], 
            linestyle='-', linewidth=2, markersize=8,
            label=f'{multiplier}x 位错密度'
        )
    
    plt.xlabel('温度 (K)', fontsize=12)
    plt.ylabel('肿胀率 (%)', fontsize=12)
    plt.title('不同位错密度下的肿胀率随温度变化', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    logger.info(f"肿胀率-温度图表已保存至: {save_path}")

def save_results_to_csv(results, filename='swelling_results.csv'):
    """将结果保存到CSV文件"""
    with open(filename, 'w') as f:
        f.write("Temperature(K),Dislocation_Multiplier,Swelling(%)\n")
        for multiplier, data in results.items():
            for temp, swelling in data:
                if swelling is not None:
                    f.write(f"{temp},{multiplier},{swelling:.6f}\n")
                else:
                    f.write(f"{temp},{multiplier},NaN\n")
    logger.info(f"结果已保存至CSV文件: {filename}")

if __name__ == "__main__":
    logger.info("======== 开始温度扫描程序 ========")
    results = run_temperature_sweep()
    
    # 打印结果
    print("\n温度扫描结果:")
    for multiplier, data in results.items():
        print(f"\n位错密度倍数: {multiplier}x")
        print("温度(K)\t肿胀率(%)")
        for temp, swelling in data:
            if swelling is not None:
                print(f"{temp}\t{swelling:.6f}")
            else:
                print(f"{temp}\t运行失败")
    
    # 保存和绘图
    save_results_to_csv(results)
    plot_swelling_vs_temperature(results)
    
    logger.info("======== 温度扫描程序完成 ========")


# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 13:54:55 2025

@author: kongxiangzhe
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from gas_swelling.models.modelrk23 import GasSwellingModel
from gas_swelling.params.parameters import create_default_parameters

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fnf_sweep.log',
    filemode='w'
)
logger = logging.getLogger('fnf_sweep')

def run_fnf_sweep(temperature=600):
    """在不同Fnf参数下运行肿胀模型并收集结果"""
    fnf_values = [1e-5, 1e-4, 1e-3, 1e-1]  # 原始值、10倍、100倍、10000倍
    results = []
    
    logger.info(f"开始Fnf参数扫描: {fnf_values}")
    sim_time = 928197.78  # 指定辐照时间
    
    for fnf in fnf_values:
        logger.info(f"===== 开始运行Fnf: {fnf} =====")
        
        try:
            # 创建参数
            params = create_default_parameters()
            
            # 固定温度
            params['temperature'] = temperature
            params['Fnf'] = fnf
            
            # 设置其他参数
            params['time_step'] = 1e-9
            params['max_time_step'] = 0.1
            params['Fnb'] = 1e-4
            params['dislocation_density'] = 7.0e13
            params['surface_energy'] = 0.5
            params['resolution_rate'] = 2.0e-5
            params['Dgb_prefactor'] = 8.55e-12
            params['Dgb_fission_term'] = 1.0e-40
            params['Dgf_multiplier'] = 1e0
            params['Dv0'] = 7.767e-10
            params['Di0'] = 1.259e-8
            params['Evm'] = 0.434
            params['Eim'] = 0.42
            params['Evfmuti'] = 1.0
            params['fission_rate'] = 5e19
            params['gas_production_rate'] = 0.5
            params['critical_radius'] = 50e-9
            params['radius_smoothing_factor'] = 0.8
            params['pressure_scaling_factor'] = 1.0
            params['vacancy_contribution_weight'] = 1.2
            
            # 创建模型
            model = GasSwellingModel(params)
            model.initial_state[2] = 4.0  # Ncb
            model.initial_state[6] = 4.0  # Ncf
            
            # 运行模拟
            
            t_eval = np.linspace(0, sim_time, 100)
            result = model.solve(t_span=(0, sim_time), t_eval=t_eval)
            # 修改run_fnf_sweep函数中的以下部分

# 运行模拟
            t_eval = np.linspace(0, sim_time, 100)
            result = model.solve(t_span=(0, sim_time), t_eval=t_eval)

# 确保正确获取时间序列数据
# 检查result中是否包含时间数据（通常是't'或'time'键）
            if 't' in result:
                time_points = result['t']
            elif 'time' in result:
                time_points = result['time']
            else:
    # 如果都没有，尝试从求解器输出中提取时间
                time_points = t_eval  # 使用我们指定的时间点
                logger.warning(f"无法从结果中获取时间序列，使用预设的t_eval")

# 计算肿胀率和燃耗
            Rcb = result['Rcb']
            Rcf = result['Rcf']
            Ccb = result['Ccb']
            Ccf = result['Ccf']

            
            V_bubble_b = (4.0/3.0) * np.pi * Rcb**3 * Ccb
            V_bubble_f = (4.0/3.0) * np.pi * Rcf**3 * Ccf
            total_V_bubble = V_bubble_b + V_bubble_f
            swelling = total_V_bubble * 100  # 肿胀率（百分比）
            
            # 计算燃耗百分比 (假设线性关系)
            burnup = (time_points / sim_time) * 0.2  # 燃耗百分比
            
            results.append({
                'fnf': fnf,
                'burnup': burnup,
                'swelling': swelling
            })
            
            logger.info(f"Fnf {fnf} 完成 - 最大肿胀率: {np.max(swelling):.6f}%")
            
        except Exception as e:
            logger.error(f"Fnf {fnf} 运行失败: {str(e)}")
            results.append({'fnf': fnf, 'error': str(e)})
    
    return results

def plot_swelling_vs_burnup(results, save_path='swelling_vs_burnup.png'):
    """绘制不同Fnf下肿胀率随燃耗变化的图表"""
    plt.figure(figsize=(10, 6))
    
    for result in results:
        if 'swelling' in result:
            plt.plot(result['burnup'], result['swelling'], 
                     label=f'Fnf = {result["fnf"]:.1e}')
    
    plt.xlabel('Burnup (%)')
    plt.ylabel('Swelling (%)')
    plt.title('Swelling vs Burnup at Different Fnf Values')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    logger.info(f"肿胀率-燃耗图表已保存至: {save_path}")

def save_results_to_csv(results, filename='fnf_sweep_results.csv'):
    """将结果保存到CSV文件"""
    with open(filename, 'w') as f:
        f.write("Fnf,Burnup(%),Swelling(%)\n")
        for result in results:
            if 'swelling' in result:
                for i in range(len(result['burnup'])):
                    f.write(f"{result['fnf']},{result['burnup'][i]},{result['swelling'][i]}\n")
    logger.info(f"结果已保存至CSV文件: {filename}")

if __name__ == "__main__":
    logger.info("======== 开始Fnf参数扫描程序 ========")
    results = run_fnf_sweep()
    
    # 打印结果摘要
    print("\nFnf参数扫描结果摘要:")
    print("Fnf\t最大肿胀率(%)")
    for result in results:
        if 'swelling' in result:
            print(f"{result['fnf']:.1e}\t{np.max(result['swelling']):.6f}")
    
    # 保存和绘图
    save_results_to_csv(results)
    plot_swelling_vs_burnup(results)
    
    logger.info("======== Fnf参数扫描程序完成 ========")