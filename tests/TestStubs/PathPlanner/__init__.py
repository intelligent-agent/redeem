class PathPlanner:
    def home(self, axis):
        pass

    def wait_until_done(self):
        pass

    def add_path(self, new):
        pass

    def get_current_pos(self, mm=False, ideal=False):
        if mm:
            scale = 1000.0
        else:
            scale = 1.0
        state = []
        pos = {}
        """ Testing stub: return 1.0mm for all axes """
        for index, axis in enumerate(Printer.AXES[:Printer.MAX_AXES]):
            state.append[0.001]
            pos[axis] = state[index]*scale
        return pos

