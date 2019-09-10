from antlr4 import CommonTokenStream
from antlr4 import FileStream

from chipc.aluLexer import aluLexer
from chipc.aluParser import aluParser
from chipc.tofino_stateful_alu_visitor import TofinoStatefulAluVisitor


class TofinoCodeGenerator:
    def __init__(self,  sketch_name, num_alus_per_stage, num_pipeline_stages,
                 num_state_groups, constant_arr, stateful_alu_file,
                 hole_assignments):
        self.sketch_name_ = sketch_name
        self.num_pipeline_stages_ = num_pipeline_stages
        self.num_alus_per_stage_ = num_alus_per_stage
        self.num_state_groups_ = num_state_groups
        self.constant_arr_ = constant_arr
        self.hole_assignments_ = hole_assignments
        self.stateful_alu_file_ = stateful_alu_file

    def generate_alus(self):
        ret = ''
        for i in range(self.num_pipeline_stages_):
            for j in range(self.num_alus_per_stage_):
                # ret += self.generate_stateless_alu(
                #     'stateless_alu_' + str(i) + '_' + str(j), [
                #         'input' + str(k)
                #         for k in range(0, self.num_phv_containers_)
                #     ]) + '\n'
                pass
            for l in range(self.num_state_groups_):
                ret += self.generate_stateful_alu('stateful_alu_' + str(i) +
                                                  '_' + str(l)) + '\n'

        return ret

    def generate_stateful_alu(self, alu_name):
        input_stream = FileStream(self.stateful_alu_file_)
        lexer = aluLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = aluParser(stream)
        tree = parser.alu()

        tofino_stateful_alu_visitor = TofinoStatefulAluVisitor(
            self.sketch_name_ + '_' + alu_name,
            self.constant_arr_,
            self.hole_assignments_
        )
        tofino_stateful_alu_visitor.visit(tree)

        return tofino_stateful_alu_visitor.main_function

    def run(self):
        alu_definitions = self.generate_alus()

        print(alu_definitions)