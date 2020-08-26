from .for_loop import ForLoopStatement
import sasoptpy


class CoForLoopStatement(ForLoopStatement):

    def __init__(self, *args):
        super().__init__(*args)
        self.keyword = 'cofor'

    @classmethod
    def cofor_loop(cls, *args):
        loop = CoForLoopStatement(*args)
        return loop
