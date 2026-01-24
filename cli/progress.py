"""
Progress Module

This module provides progress tracking and status updates during
simulation execution. It integrates with tqdm for progress bars
and handles callback registration with the solver.

Classes:
    ProgressTracker: Manages progress display and updates

Functions:
    create_progress_tracker: Factory function to create a ProgressTracker instance
"""

from typing import Callable, Optional
import sys


class ProgressTracker:
    """
    Progress tracker for simulation execution.

    This class manages progress display using tqdm and provides
    callbacks for integration with the numerical solver.

    Attributes:
        total_steps: Total number of simulation steps
        current_step: Current step number
        verbose: Whether to show detailed progress
        pbar: tqdm progress bar instance (if tqdm is available)
        use_tqdm: Whether tqdm is available for use

    Example:
        >>> tracker = ProgressTracker(100, verbose=True)
        >>> for i in range(100):
        ...     tracker.update(i, "Processing step")
        >>> tracker.close()
    """

    def __init__(self, total_steps: int, verbose: bool = False, desc: str = "Simulating"):
        """
        Initialize progress tracker.

        Args:
            total_steps: Total number of steps to track
            verbose: Whether to show detailed progress information
            desc: Description for the progress bar (default: "Simulating")
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.verbose = verbose
        self.desc = desc
        self.pbar = None
        self.use_tqdm = False

        # Try to import tqdm
        try:
            from tqdm import tqdm
            self.tqdm = tqdm
            self.use_tqdm = True
        except ImportError:
            self.tqdm = None
            self.use_tqdm = False

        # Initialize tqdm progress bar if available
        if self.use_tqdm:
            self.pbar = self.tqdm(
                total=total_steps,
                desc=desc,
                disable=not verbose,
                file=sys.stdout,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            )

    def update(self, step: int, message: str = "") -> None:
        """
        Update progress to specified step.

        Args:
            step: Current step number
            message: Optional status message to display

        Example:
            >>> tracker = ProgressTracker(100)
            >>> tracker.update(50, "Halfway done")
        """
        # Calculate the increment
        increment = step - self.current_step
        self.current_step = step

        # Update tqdm progress bar if available
        if self.use_tqdm and self.pbar is not None:
            self.pbar.update(increment)
            if message:
                self.pbar.set_postfix_str(message)
        elif self.verbose and message:
            # Fallback to simple print if tqdm is not available
            progress_pct = (step / self.total_steps) * 100
            print(f"{self.desc}: {progress_pct:.1f}% - {message}")

    def get_callback(self) -> Optional[Callable]:
        """
        Get a callback function for solver integration.

        This returns a callback function that can be passed to the
        numerical solver to update progress during integration.

        Returns:
            Callback function compatible with scipy.integrate.solve_ivp,
            or None if total_steps is invalid

        Example:
            >>> tracker = ProgressTracker(100)
            >>> callback = tracker.get_callback()
            >>> # Pass callback to solver: solver.solve(fun, t_span, y0, callback=callback)
        """
        if self.total_steps <= 0:
            return None

        def callback(t, y):
            """
            Callback function for solver integration.

            Args:
                t: Current time
                y: Current state vector

            Returns:
                False to continue integration (for scipy.integrate.solve_ivp)
            """
            # Update progress bar
            if self.use_tqdm and self.pbar is not None:
                self.pbar.update(1)
            elif self.verbose:
                progress_pct = (self.current_step / self.total_steps) * 100
                print(f"\r{self.desc}: {progress_pct:.1f}%", end='')

            self.current_step += 1

            # Return False to continue integration (scipy callback convention)
            return False

        return callback

    def set_description(self, desc: str) -> None:
        """
        Update the progress bar description.

        Args:
            desc: New description for the progress bar

        Example:
            >>> tracker = ProgressTracker(100)
            >>> tracker.set_description("Solving ODEs")
        """
        self.desc = desc
        if self.use_tqdm and self.pbar is not None:
            self.pbar.set_description(desc)

    def close(self) -> None:
        """
        Close progress bar and clean up resources.

        This should be called when the simulation is complete to
        ensure the progress bar is properly closed.

        Example:
            >>> tracker = ProgressTracker(100)
            >>> tracker.update(100)
            >>> tracker.close()
        """
        if self.use_tqdm and self.pbar is not None:
            self.pbar.close()
            self.pbar = None
        elif self.verbose:
            # Print newline to finish the progress line
            print()


def create_progress_tracker(total_steps: int, verbose: bool = False, desc: str = "Simulating") -> ProgressTracker:
    """
    Factory function to create a progress tracker.

    This function provides a convenient way to create a ProgressTracker
    with consistent parameters.

    Args:
        total_steps: Total number of steps to track
        verbose: Whether to show detailed progress
        desc: Description for the progress bar (default: "Simulating")

    Returns:
        ProgressTracker instance

    Example:
        >>> tracker = create_progress_tracker(100, verbose=True)
        >>> for i in range(100):
        ...     tracker.update(i)
        >>> tracker.close()
    """
    return ProgressTracker(total_steps, verbose, desc)
