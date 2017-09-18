from logging import debug, info
import numpy as np
import pandas as pd

from .detectorbase import DetectorBase


class StaLtaDetect(DetectorBase):
    def __init__(self, trace, sampling_rate):
        """
        Create a new Detector object

        Args:
            trace (np.ndarray): raw trace
            sampling_rate (int): Sample rate of trace in Hz
        """
        super().__init__(trace, sampling_rate)
        self.trigger_values = None

    def detect(self, short, long, nstds=1, trigger_len=5000):
        """
        Run a hackish STA-LTA like detection on trace. Looks for short
        window means above nstds standard deviations from the long window
        mean for more than trigger_len observations.
        
        Args:
            short (int): number of ms for short window
            long (int): number of ms for long window
            nstds (float): number of standard deviations from long window
                mean to trigger on
            trigger_len (int): length in ms of short mean observations
                being above nstds to trigger on
            
        Yields:
            (time from start, long window mean, short window mean)        
        """
        trigger_values = []

        long_win_len = int(long / self.interval)
        short_win_len = int(short / self.interval)
        iter_len = 1
        # Convert from ms to number of obs
        trigger_len = int(trigger_len / self.interval)
        debug("Window lengths: {}, {} ({}s, {}s)".format(
            long_win_len, short_win_len, long/1000, short/1000))
        i = long_win_len + short_win_len
        triggered = False
        off_threshold = 0
        triggered_obs = 0
        while i + short_win_len < len(self.trace):
            long_window = self.abs[
                i - long_win_len - short_win_len:
                i - short_win_len
            ]
            long_win_mean = np.mean(long_window)
            long_win_std = np.std(long_window)
            short_win_mean = np.mean(
                self.abs[i - short_win_len:i])
            trigger_values.append((
                i * self.interval,
                short_win_mean,
                long_win_mean,
                long_win_std * nstds
            ))
            if not triggered:
                trigger_val = long_win_mean + long_win_std * nstds
                if short_win_mean > trigger_val:
                    off_threshold = long_win_mean
                    triggered = True
                    triggered_obs = 1
            else:  # if triggered
                triggered_obs += iter_len
                if short_win_mean < off_threshold:  # trigger over
                    triggered = False
                    if triggered_obs > trigger_len:
                        yield(
                            int(i - triggered_obs - (short_win_len / 2)) * self.interval,
                            i * self.interval
                        )
                    triggered_obs = 0
            i += iter_len
        # Get trigger values
        self.trigger_values = pd.DataFrame(
            trigger_values,
            columns=("t", "sm", "lm", "trigger"),
        )
