from stateful_aluParser import stateful_aluParser
from stateful_aluVisitor import stateful_aluVisitor
from overrides import overrides

# Visitor class to generate Sketch code from a stateful_alu specification in a .stateful_alu file
class StatefulAluSketchGenerator(stateful_aluVisitor):
  def __init__(self, stateful_alu_file, stateful_alu_name):
    self.stateful_alu_name = stateful_alu_name
    self.stateful_alu_file = stateful_alu_file
    self.mux3Count = 0
    self.mux2Count = 0
    self.relopCount = 0
    self.optCount = 0
    self.constCount = 0
    self.helperFunctionStrings = "\n\n\n"
    self.globalholes = dict()
    self.stateful_alu_args = dict()
    self.mainFunction = ""
    self.num_packet_fields = 0

  def add_hole(self, hole_name, hole_width):
    prefixed_hole = self.stateful_alu_name + "_" + hole_name
    assert(prefixed_hole + "_global" not in self.globalholes)
    self.globalholes[prefixed_hole + "_global"] = hole_width
    assert(hole_name not in self.stateful_alu_args)
    self.stateful_alu_args[hole_name] = hole_width

  @overrides
  def visitStateful_alu(self, ctx):
    self.mainFunction += "int " + self.stateful_alu_name + "("
    self.visit(ctx.getChild(0, stateful_aluParser.State_varsContext))
    self.mainFunction += ", "
    self.visit(ctx.getChild(0, stateful_aluParser.Packet_fieldsContext))
    self.mainFunction += ", %s) {\n int old_state = state_1;" # The %s is for hole arguments, which are added below.
    self.visit(ctx.getChild(0, stateful_aluParser.Guarded_updatesContext))
    self.mainFunction += "\n; return old_state;\n}"
    argument_string = ",".join(["int " + hole for hole in sorted(self.stateful_alu_args)])
    self.mainFunction = self.mainFunction%argument_string

  @overrides
  def visitState_var(self, ctx):
    self.mainFunction += ctx.getText()

  @overrides
  def visitPacket_field(self, ctx):
    self.mainFunction += ctx.getText()

  @overrides
  def visitState_vars(self, ctx):
    self.mainFunction +=  "ref int "
    self.visit(ctx.getChild(0, stateful_aluParser.State_varContext))
    assert(ctx.getChildCount() == 1), "We currently only handle 1 state variable in an atom."

  @overrides
  def visitPacket_fields(self, ctx):
    self.mainFunction += "int "
    self.mainFunction += ctx.getChild(0, stateful_aluParser.Packet_fieldContext).getText() + ","
    self.num_packet_fields = 1
    if (ctx.getChildCount() > 1):
      for i in range(1, ctx.getChildCount()):
        self.visit(ctx.getChild(i))
        self.num_packet_fields += 1
    self.mainFunction = self.mainFunction[:-1] # Trim out the last comma

  @overrides
  def visitPacket_field_with_comma(self, ctx):
    self.mainFunction += "int "
    assert(ctx.getChild(0).getText() == ",")
    self.mainFunction += ctx.getChild(1).getText() + ","

  @overrides
  def visitMux2(self, ctx):
    self.mainFunction += self.stateful_alu_name + "_" + "Mux2_" + str(self.mux2Count) + "("
    self.visit(ctx.getChild(0, stateful_aluParser.ExprContext))
    self.mainFunction += ","
    self.visit(ctx.getChild(1, stateful_aluParser.ExprContext))
    self.mainFunction += "," + "Mux2_" + str(self.mux2Count) + ")"
    self.generateMux2()
    self.mux2Count += 1

  @overrides
  def visitMux3(self, ctx):
    self.mainFunction += self.stateful_alu_name + "_" + "Mux3_" + str(self.mux3Count) + "("
    self.visit(ctx.getChild(0, stateful_aluParser.ExprContext))
    self.mainFunction += ","
    self.visit(ctx.getChild(1, stateful_aluParser.ExprContext))
    self.mainFunction += ","
    self.visit(ctx.getChild(2, stateful_aluParser.ExprContext))
    self.mainFunction += "," + "Mux3_" + str(self.mux3Count) + ")"
    self.generateMux3()
    self.mux3Count += 1

  @overrides
  def visitOpt(self, ctx):
    self.mainFunction += self.stateful_alu_name + "_" + "Opt_" + str(self.optCount) + "("
    self.visitChildren(ctx)
    self.mainFunction += "," + "Opt_" + str(self.optCount) + ")"
    self.generateOpt()
    self.optCount += 1

  @overrides
  def visitRelOp(self, ctx):
    self.mainFunction += self.stateful_alu_name + "_" + "rel_op_" + str(self.relopCount) + "("
    self.visit(ctx.getChild(0, stateful_aluParser.ExprContext))
    self.mainFunction += ","
    self.visit(ctx.getChild(1, stateful_aluParser.ExprContext))
    self.mainFunction += "," + "rel_op_" + str(self.relopCount) + ")"
    self.generateRelOp()
    self.relopCount += 1

  @overrides
  def visitTrue(self, ctx):
    self.mainFunction += "true"

  @overrides
  def visitConstant(self, ctx):
    self.mainFunction += self.stateful_alu_name + "_" + "C_" + str(self.constCount) + "("
    self.mainFunction += "const_" + str(self.constCount) + ")"
    self.generateConstant()
    self.constCount += 1

  @overrides
  def visitUpdate(self, ctx):
    self.visit(ctx.getChild(0, stateful_aluParser.State_varContext))
    self.mainFunction += " = "
    self.visit(ctx.getChild(0, stateful_aluParser.ExprContext))

  @overrides
  def visitGuarded_update(self, ctx):
    self.mainFunction += "if("
    self.visit(ctx.getChild(0, stateful_aluParser.GuardContext))
    self.mainFunction += ")"
    self.mainFunction += "{\n\t"
    self.visit(ctx.getChild(0, stateful_aluParser.UpdateContext))
    self.mainFunction += ";\n}"

  @overrides
  def visitExprWithOp(self, ctx):
    self.visit(ctx.getChild(0, stateful_aluParser.ExprContext))
    self.mainFunction += ctx.getChild(1).getText()
    self.visit(ctx.getChild(1, stateful_aluParser.ExprContext))

  def generateMux2(self):
    self.helperFunctionStrings += "int " + self.stateful_alu_name + "_" + "Mux2_" + str(self.mux2Count) +  """(int op1, int op2, int choice) {
    if (choice == 0) return op1;
    else if (choice == 1) return op2;
    else assert(false);
    } \n\n"""
    self.add_hole("Mux2_" + str(self.mux2Count), 2);

  def generateMux3(self):
    self.helperFunctionStrings += "int " + self.stateful_alu_name + "_" + "Mux3_" + str(self.mux3Count) + """(int op1, int op2, int op3, int choice) {
    if (choice == 0) return op1;
    else if (choice == 1) return op2;
    else if (choice == 2) return op3;
    else assert(false);
    } \n\n"""
    self.add_hole("Mux3_" + str(self.mux3Count), 2)

  def generateRelOp(self):
    self.helperFunctionStrings += "bit " + self.stateful_alu_name + "_" + "rel_op_" + str(self.relopCount) + """(int operand1, int operand2, int opcode) {
    if (opcode == 0) {
      return operand1 != operand2;
    } else if (opcode == 1) {
      return operand1 < operand2;
    } else if (opcode == 2) {
      return operand1 > operand2;
    } else {
      assert(opcode == 3);
      return operand1 == operand2;
    }
    } \n\n"""
    self.add_hole("rel_op_" + str(self.relopCount), 2)

  def generateConstant(self):
    self.helperFunctionStrings += "int " + self.stateful_alu_name + "_" + "C_" + str(self.constCount) + """(int const) {
    return const;
    }\n\n"""
    self.add_hole("const_" + str(self.constCount), 2)

  def generateOpt(self):
    self.helperFunctionStrings += "int " + self.stateful_alu_name + "_" + "Opt_" + str(self.optCount) + """(int op1, int enable) {
    if (enable != 0) return 0;
    return op1;
    } \n\n"""
    self.add_hole("Opt_" + str(self.optCount), 1)