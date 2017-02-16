class HardwareBase(object):
    def __init__(self, config):
        pass

    def on_before_execution(self):
        """
        This callback will be called when a testbed is about to run a task. This allows the
        hardware to prepare before the task is running.
        """
        pass

    def on_execute(self):
        """
        This callback is called when the task starts.
        """
        pass

    def on_terminate(self):
        """
        This callback is called when other hardware sends a signal to stop the task, or
        hardware engine sends a signal because the hard deadline is passed. The callback
        should quickly terminate all on going jobs and return results to hardware engine.

        Return:
          - dict_output_binary: A dictionary of output files in binary format
        """
        pass
    
    def on_reset_after_execution(self):
        """
        After the hardware engine acquire output from all hardware pieces, the hardware engine
        will call this method for the hardware itself to clean up. Implementing this method
        is optional since you may consider integrating the procedure into on_before_execution()
        method.
        """
        pass

