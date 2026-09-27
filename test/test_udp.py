import os
from unittest_utils import RDLSourceTestCase
from systemrdl import RDLCompiler
from systemrdl.messages import RDLCompileError
from systemrdl import component as comp
from systemrdl.udp import UDPDefinition
from systemrdl import builtin_udps
from systemrdl.rdltypes import NoValue, ArrayedType, RefType

this_dir = os.path.dirname(os.path.realpath(__file__))

class TestUDP(RDLSourceTestCase):

    def test_15_2_2_ex1(self):
        root = self.compile(
            ["rdl_src/udp_15.2.2_ex1.rdl"],
            "foo"
        )

        foo    = root.find_by_path("foo")
        bar    = root.find_by_path("foo.bar")
        field1 = root.find_by_path("foo.bar.field1")
        field2 = root.find_by_path("foo.bar.field2")

        with self.subTest("foo"):
            self.assertIs(foo.get_property('some_ref_p'), None)
            self.assertIs(foo.get_property('a_map_p'), NoValue)

        with self.subTest("bar"):
            self.assertIs(bar.get_property('some_ref_p'), None)
            self.assertEqual(bar.get_property('some_num_p'), 0x20)

        with self.subTest("field1"):
            self.assertEqual(field1.get_property('some_ref_p'), field2)
            self.assertIs(field1.get_property('some_bool_p'), False)
            self.assertIs(field1.get_property('some_num_p'), None)

        with self.subTest("field2"):
            self.assertIs(field2.get_property('some_ref_p'), None)
            self.assertIs(field2.get_property('some_bool_p'), True)
            self.assertIs(field2.get_property('some_num_p'), 0x10)

    def test_15_2_2_ex2(self):
        root = self.compile(
            ["rdl_src/udp_15.2.2_ex2.rdl"],
            "top"
        )

        f = root.find_by_path("top.regA.f")
        self.assertEqual(f.get_property('my_enc_prop').value, 0)
        self.assertEqual(f.get_property('my_enc_prop').name, "alpha")

    def test_builtin_udp(self):
        class MyUDP(UDPDefinition):
            name = "int_udp"
            valid_type = int
            default_assignment = 123

        rdlc = RDLCompiler()
        rdlc.register_udp(MyUDP, soft=False)
        rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_builtin.rdl"))
        root = rdlc.elaborate("top")

        top    = root.find_by_path("top")
        reg1   = root.find_by_path("top.reg1")
        field1 = root.find_by_path("top.reg1.field1")

        self.assertIs(top.get_property('int_udp'), 43)
        self.assertIs(reg1.get_property('int_udp'), 42)
        self.assertIs(field1.get_property('int_udp'), 123)

    def test_builtin_udp_validate(self):
        class MyUDP(UDPDefinition):
            name = "int_udp"
            valid_type = int
            default_assignment = 123

            def validate(self, node, value) -> None:
                self.msg.error("my error msg")

        rdlc = RDLCompiler()
        rdlc.register_udp(MyUDP, soft=False)
        rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_builtin.rdl"))
        with self.assertRaises(RDLCompileError):
            rdlc.elaborate("top")

    def test_udp_types(self):
        root = self.compile(
            ["rdl_src/udp_types.rdl"],
            "top"
        )
        field = root.find_by_path("top.x.defaults")
        self.assertEqual(field.get_property("int_udp"), 123)
        self.assertEqual(field.get_property("bool_udp"), False)

    def test_soft_udp_types(self):
        class IntUDP(UDPDefinition):
            name = "int_udp"
            valid_type = int
            default_assignment = 123
        class BoolUDP(UDPDefinition):
            name = "bool_udp"
            valid_type = bool
            default_assignment = False
        rdlc = RDLCompiler()
        rdlc.register_udp(IntUDP)
        rdlc.register_udp(BoolUDP)
        rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_types.rdl"))
        root = rdlc.elaborate("top")

        field = root.find_by_path("top.x.defaults")
        self.assertEqual(field.get_property("int_udp"), 123)
        self.assertEqual(field.get_property("bool_udp"), False)

    def test_soft_udp_undeclared(self):
        class MyUDP(UDPDefinition):
            name = "int_udp"
            valid_type = int
            default_assignment = 123
        rdlc = RDLCompiler()
        rdlc.register_udp(MyUDP)
        with self.assertRaises(RDLCompileError):
            rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_builtin.rdl"))

    def test_soft_udp_query(self):
        class MyUDP(UDPDefinition):
            name = "int_udp"
            valid_type = int
            default_assignment = 123
        rdlc = RDLCompiler()
        rdlc.register_udp(MyUDP)
        rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_15.2.2_ex2.rdl"))
        root = rdlc.elaborate("top")

        f = root.find_by_path("top.regA.f")
        self.assertIsNone(f.get_property('int_udp'))

    def test_soft_udp_success(self):
        class MyUDP(UDPDefinition):
            name = "a_map_p"
            valid_type = str
            valid_components = {comp.Addrmap, comp.Regfile}
        rdlc = RDLCompiler()
        rdlc.register_udp(MyUDP)
        rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_15.2.2_ex1.rdl"))
        rdlc.elaborate("foo")

    def test_soft_udp_conflict(self):
        class MyUDP(UDPDefinition):
            name = "a_map_p"
            valid_type = int # src defines as a string
            valid_components = {comp.Addrmap, comp.Regfile}
        rdlc = RDLCompiler()
        rdlc.register_udp(MyUDP)
        with self.assertRaises(RDLCompileError):
            rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_15.2.2_ex1.rdl"))

    def test_soft_udp_dupe(self):
        class MyUDP(UDPDefinition):
            name = "bool_udp"
            valid_type = bool
            valid_components = {comp.Field}
        rdlc = RDLCompiler()
        rdlc.register_udp(MyUDP)
        with self.assertRaises(RDLCompileError):
            rdlc.compile_file(os.path.join(this_dir, "rdl_err_src/err_duplicate_udp.rdl"))

    def test_list_udps(self):

        class MyUDP1(UDPDefinition):
            name = "int_udp"
            valid_type = int
            default_assignment = 123

        class MyUDP2(UDPDefinition):
            name = "int_udp_soft"
            valid_type = int
            default_assignment = 123

        rdlc = RDLCompiler()
        rdlc.register_udp(MyUDP1, soft=False)
        rdlc.register_udp(MyUDP2, soft=True)
        rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_15.2.2_ex1.rdl"))
        rdlc.elaborate("foo")

        self.assertEqual(
            sorted(rdlc.list_udps()),
            [
                'a_map_p',
                'int_udp',
                'some_bool_p',
                'some_num_p',
                'some_ref_p',
            ]
        )

    def test_udp_arrays(self):
        root = self.compile(
            ["rdl_src/udp_arrays.rdl"],
            "top"
        )
        top = root.top
        r1 = top.find_by_path("r1")
        r1_f1 = top.find_by_path("r1.f1")
        r1_f2 = top.find_by_path("r1.f2")
        r2 = top.find_by_path("r2")
        r2_f1 = top.find_by_path("r2.f1")
        r2_f2 = top.find_by_path("r2.f2")
        r3 = top.find_by_path("r3")
        r3_f1 = top.find_by_path("r3.f1")
        r3_f2 = top.find_by_path("r3.f2")

        with self.subTest("top.ref_array"):
            ref_array = top.get_property('ref_array')
            self.assertEqual(len(ref_array), 3)
            self.assertEqual(ref_array[0], r1)
            self.assertEqual(ref_array[1], r2_f1)
            self.assertEqual(ref_array[2].node, r3_f2)
            self.assertEqual(ref_array[2].name, "anded")

        with self.subTest("top.reg_array"):
            self.assertListEqual(
                top.get_property('reg_array'),
                [r1, r2]
            )

        with self.subTest("top.field_array"):
            self.assertListEqual(
                top.get_property('field_array'),
                [r1_f1, r2_f1, r3_f1]
            )

        with self.subTest("top.int_array"):
            self.assertListEqual(
                top.get_property('int_array'),
                [10, 20]
            )

        with self.subTest("top.struct_array"):
            struct_array = top.get_property('struct_array')
            self.assertEqual(len(struct_array), 3)

            self.assertEqual(struct_array[0].type_name, "my_struct")
            self.assertEqual(set(struct_array[0].members.keys()), {"my_bool", "my_string"})
            self.assertEqual(struct_array[0].my_bool, True)
            self.assertEqual(struct_array[0].my_string, "hey")

            self.assertEqual(struct_array[1].type_name, "my_struct")
            self.assertEqual(set(struct_array[1].members.keys()), {"my_bool", "my_string"})
            self.assertEqual(struct_array[1].my_bool, False)
            self.assertEqual(struct_array[1].my_string, "hello")

            self.assertEqual(struct_array[2].type_name, "my_extended_struct")
            self.assertEqual(set(struct_array[2].members.keys()), {"my_bool", "my_string", "my_int"})
            self.assertEqual(struct_array[2].my_bool, False)
            self.assertEqual(struct_array[2].my_string, "extended")
            self.assertEqual(struct_array[2].my_int, 42)



        with self.subTest("sub1"):
            sub1 = top.find_by_path("sub1")
            x_f1 = top.find_by_path("sub1.x.f1")
            x_f2 = top.find_by_path("sub1.x.f2")
            y_f1 = top.find_by_path("sub1.y.f1")
            y_f2 = top.find_by_path("sub1.y.f2")
            self.assertListEqual(
                sub1.get_property('ref_array'),
                [x_f1, x_f2, y_f1, y_f2]
            )

        with self.subTest("sub2"):
            sub2 = top.find_by_path("sub2")
            a_f1 = top.find_by_path("sub2.a.f1")
            b_f2 = top.find_by_path("sub2.b.f2")
            prop = sub2.get_property('ref_array')
            self.assertEqual(len(prop), 2)
            self.assertEqual(prop[0].node, a_f1)
            self.assertEqual(prop[0].name, "anded")
            self.assertEqual(prop[1].node, b_f2)
            self.assertEqual(prop[1].name, "anded")

        with self.subTest("sub3"):
            sub3 = top.find_by_path("sub3")
            a_f1 = top.find_by_path("sub2.a.f1")
            x_f2 = top.find_by_path("sub1.x.f2")
            self.assertListEqual(
                sub3.get_property('ref_array'),
                [a_f1, x_f2]
            )

    def test_builtin_udp_arrays(self):
        class RefArrayUDP(UDPDefinition):
            name = "ref_array"
            valid_type = ArrayedType(RefType)
            valid_components = {comp.Addrmap}

        class RegArrayUDP(UDPDefinition):
            name = "reg_array"
            valid_type = ArrayedType(comp.Reg)
            valid_components = {comp.Addrmap}

        class FieldArrayUDP(UDPDefinition):
            name = "field_array"
            valid_type = ArrayedType(comp.Field)
            valid_components = {comp.Addrmap}

        class IntArrayUDP(UDPDefinition):
            name = "int_array"
            valid_type = ArrayedType(int)
            valid_components = {comp.Addrmap}

        rdlc = RDLCompiler()
        rdlc.register_udp(RefArrayUDP)
        rdlc.register_udp(RegArrayUDP)
        rdlc.register_udp(FieldArrayUDP)
        rdlc.register_udp(IntArrayUDP)
        rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_arrays.rdl"))
        root = rdlc.elaborate("top")

    def test_anonymous_field(self):
        root = self.compile(["rdl_src/udp_anonymous.rdl"], "top")

        epid = root.find_by_path("top.EPID")
        status = root.find_by_path("top.STATUS")
        ctrl = root.find_by_path("top.CTRL")
        multi = root.find_by_path("top.MULTI")

        self.assertTrue(epid.fields()[0].is_anonymous)
        self.assertEqual(epid.anonymous_field, epid.fields()[0])
        self.assertEqual(status.anonymous_field, status.fields()[0])
        self.assertFalse(ctrl.fields()[0].is_anonymous)
        self.assertIsNone(ctrl.anonymous_field)
        self.assertIsNone(multi.anonymous_field)
        self.assertIs(multi.fields()[0].get_property('anonymous'), False)

    def test_anonymous_field_undeclared(self):
        # Soft UDP: not declared in the RDL, so it is implicitly never set
        root = self.compile(["rdl_src/udp_anonymous_undeclared.rdl"], "top")
        epid = root.find_by_path("top.EPID")
        self.assertFalse(epid.fields()[0].is_anonymous)
        self.assertIsNone(epid.anonymous_field)

    def test_anonymous_field_implicit(self):
        # Built-in UDP is usable without a declaration, including via dynamic assignment
        root = self.compile(["rdl_src/udp_anonymous_implicit.rdl"], "top")
        self.assertIsNotNone(root.find_by_path("top.epid").anonymous_field)
        self.assertIsNotNone(root.find_by_path("top.other").anonymous_field)

    def test_anonymous_field_errors(self):
        self.assertRDLCompileError(
            ["rdl_err_src/err_udp_anonymous.rdl"],
            "err_anon_multi_field",
            r"Field 'a' is marked as anonymous, but register 'r1' contains 2 fields"
        )

    def test_builtin_udp_declarations(self):
        # Soft UDP registration errors if the RDL declaration differs from the
        # Python definition, so this keeps the two in sync
        rdlc = RDLCompiler()
        rdlc.compile_file(builtin_udps.RDL_PATH)
        rdlc.compile_file(os.path.join(this_dir, "rdl_src/udp_anonymous_undeclared.rdl"))
        rdlc.elaborate("top")
        self.assertIn("anonymous", rdlc.list_udps())
