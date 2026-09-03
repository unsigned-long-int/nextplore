import unittest

from svc_llm_inference_contracts.models import (
    DataStoreEntry,
    LlmOutputSpecs,
    SchemaEntry,
)

from llm_inference_service.services.rag_pipeline.ai_adapter.llm_output_specs_tool_adapter import (
    build_tool_schema,
)

COLUMNS_EMP = ["employee_id", "full_name", "department_id"]
COLUMNS_DEPT = ["department_id", "name"]

QUALIFIED_COLUMNS_EMP = [
    "hr.employees.employee_id",
    "hr.employees.full_name",
    "hr.employees.department_id",
]
QUALIFIED_COLUMNS_DEPT = ["hr.departments.department_id", "hr.departments.name"]
ALL_QUALIFIED_COLUMNS = QUALIFIED_COLUMNS_EMP + QUALIFIED_COLUMNS_DEPT


def make_llm_output_specs() -> LlmOutputSpecs:
    return LlmOutputSpecs(
        datastore_registry_repr='{"int-1": {"hr": {"employees": ["employee_id", "full_name", "department_id"], "departments": ["department_id", "name"]}}}',
        datastores_enum=["int-1"],
        schemas_enum=["hr"],
        tables_enum=["employees", "departments"],
        columns_enum=["employee_id", "full_name", "department_id", "name"],
        filter_op_enum=["==", "in", "like", ">", "<", ">=", "<="],
        agg_funcs_enum=["avg", "sum", "min", "max", "count"],
        table_columns_registry={
            "int-1": DataStoreEntry(
                schemas={
                    "hr": SchemaEntry(
                        tables={
                            "employees": COLUMNS_EMP,
                            "departments": COLUMNS_DEPT,
                        }
                    )
                }
            )
        },
    )


def make_single_table_specs() -> LlmOutputSpecs:
    return LlmOutputSpecs(
        datastore_registry_repr='{"int-1": {"hr": {"employees": ["employee_id"]}}}',
        datastores_enum=["int-1"],
        schemas_enum=["hr"],
        tables_enum=["employees"],
        columns_enum=["employee_id"],
        filter_op_enum=["==", "in"],
        agg_funcs_enum=["count"],
        table_columns_registry={
            "int-1": DataStoreEntry(
                schemas={"hr": SchemaEntry(tables={"employees": ["employee_id"]})}
            )
        },
    )


class TestBuildToolSchemaStructure(unittest.TestCase):
    def setUp(self):
        self.specs = make_llm_output_specs()
        self.tools = build_tool_schema(self.specs)
        self.tool = self.tools[0]
        self.params = self.tool["function"]["parameters"]
        self.props = self.params["properties"]

    def test_returns_list_with_one_tool(self):
        self.assertEqual(len(self.tools), 1)

    def test_tool_type_is_function(self):
        self.assertEqual(self.tool["type"], "function")

    def test_function_name_is_generate_orm_class(self):
        self.assertEqual(self.tool["function"]["name"], "generate_orm_class")

    def test_strict_is_true(self):
        self.assertTrue(self.tool["function"]["strict"])

    def test_description_present(self):
        self.assertIn("description", self.tool["function"])

    def test_parameters_type_is_object(self):
        self.assertEqual(self.params["type"], "object")

    def test_additional_properties_false(self):
        self.assertFalse(self.params["additionalProperties"])

    def test_required_fields(self):
        self.assertEqual(
            set(self.params["required"]),
            {
                "datastore",
                "class_name",
                "column_names",
                "column_filters",
                "column_aggregates",
            },
        )

    def test_no_one_of_present(self):
        self.assertNotIn("oneOf", self.params)


class TestBuildToolSchemaDataStore(unittest.TestCase):
    def setUp(self):
        self.specs = make_llm_output_specs()
        self.props = build_tool_schema(self.specs)[0]["function"]["parameters"][
            "properties"
        ]

    def test_datastore_enum_matches(self):
        self.assertEqual(self.props["datastore"]["enum"], self.specs.datastores_enum)

    def test_datastore_description_contains_registry_repr(self):
        self.assertIn(
            self.specs.datastore_registry_repr, self.props["datastore"]["description"]
        )

    def test_class_name_present(self):
        self.assertIn("class_name", self.props)

    def test_class_name_has_description(self):
        self.assertIn("description", self.props["class_name"])


class TestBuildToolSchemaQualifiedColumns(unittest.TestCase):
    def setUp(self):
        self.specs = make_llm_output_specs()
        self.props = build_tool_schema(self.specs)[0]["function"]["parameters"][
            "properties"
        ]

    def test_column_names_type_is_array(self):
        self.assertEqual(self.props["column_names"]["type"], "array")

    def test_column_names_items_type_is_string(self):
        self.assertEqual(self.props["column_names"]["items"]["type"], "string")

    def test_column_names_enum_contains_all_qualified_columns(self):
        enum = self.props["column_names"]["items"]["enum"]
        for col in ALL_QUALIFIED_COLUMNS:
            self.assertIn(col, enum)

    def test_column_names_enum_uses_qualified_format(self):
        enum = self.props["column_names"]["items"]["enum"]
        for col in enum:
            self.assertEqual(len(col.split(".")), 3)

    def test_column_names_enum_does_not_contain_unqualified_columns(self):
        enum = self.props["column_names"]["items"]["enum"]
        for col in COLUMNS_EMP + COLUMNS_DEPT:
            self.assertNotIn(col, enum)

    def test_column_names_description_present(self):
        self.assertIn("description", self.props["column_names"])

    def test_single_table_produces_correct_qualified_columns(self):
        props = build_tool_schema(make_single_table_specs())[0]["function"][
            "parameters"
        ]["properties"]
        self.assertEqual(
            props["column_names"]["items"]["enum"], ["hr.employees.employee_id"]
        )

    def test_empty_registry_produces_empty_enum(self):
        specs = LlmOutputSpecs(
            datastore_registry_repr="{}",
            datastores_enum=[],
            schemas_enum=[],
            tables_enum=[],
            columns_enum=[],
            filter_op_enum=["=="],
            agg_funcs_enum=["count"],
            table_columns_registry={},
        )
        props = build_tool_schema(specs)[0]["function"]["parameters"]["properties"]
        self.assertEqual(props["column_names"]["items"]["enum"], [])


class TestBuildToolSchemaFilters(unittest.TestCase):
    def setUp(self):
        self.specs = make_llm_output_specs()
        self.filter_schema = build_tool_schema(self.specs)[0]["function"]["parameters"][
            "properties"
        ]["column_filters"]
        self.filter_items = self.filter_schema["items"]

    def test_column_filters_type_is_array(self):
        self.assertEqual(self.filter_schema["type"], "array")

    def test_filter_items_type_is_object(self):
        self.assertEqual(self.filter_items["type"], "object")

    def test_filter_required_fields(self):
        self.assertEqual(
            set(self.filter_items["required"]), {"operator", "value", "filter_column"}
        )

    def test_filter_additional_properties_false(self):
        self.assertFalse(self.filter_items["additionalProperties"])

    def test_operator_enum_matches_filter_op_enum(self):
        self.assertEqual(
            self.filter_items["properties"]["operator"]["enum"],
            self.specs.filter_op_enum,
        )

    def test_filter_column_enum_contains_all_qualified_columns(self):
        enum = self.filter_items["properties"]["filter_column"]["enum"]
        for col in ALL_QUALIFIED_COLUMNS:
            self.assertIn(col, enum)

    def test_filter_column_enum_uses_qualified_format(self):
        enum = self.filter_items["properties"]["filter_column"]["enum"]
        for col in enum:
            self.assertEqual(len(col.split(".")), 3)

    def test_filter_column_enum_does_not_contain_unqualified_columns(self):
        enum = self.filter_items["properties"]["filter_column"]["enum"]
        for col in COLUMNS_EMP + COLUMNS_DEPT:
            self.assertNotIn(col, enum)

    def test_value_accepts_number_and_string(self):
        self.assertEqual(
            self.filter_items["properties"]["value"]["type"], ["number", "string"]
        )

    def test_filter_description_present(self):
        self.assertIn("description", self.filter_schema)

    def test_operator_description_present(self):
        self.assertIn("description", self.filter_items["properties"]["operator"])


class TestBuildToolSchemaAggregates(unittest.TestCase):
    def setUp(self):
        self.specs = make_llm_output_specs()
        self.agg_schema = build_tool_schema(self.specs)[0]["function"]["parameters"][
            "properties"
        ]["column_aggregates"]
        self.agg_items = self.agg_schema["items"]

    def test_column_aggregates_type_is_array(self):
        self.assertEqual(self.agg_schema["type"], "array")

    def test_agg_items_type_is_object(self):
        self.assertEqual(self.agg_items["type"], "object")

    def test_agg_required_fields(self):
        self.assertEqual(set(self.agg_items["required"]), {"agg_func", "agg_column"})

    def test_agg_additional_properties_false(self):
        self.assertFalse(self.agg_items["additionalProperties"])

    def test_agg_func_enum_matches_agg_funcs_enum(self):
        self.assertEqual(
            self.agg_items["properties"]["agg_func"]["enum"], self.specs.agg_funcs_enum
        )

    def test_agg_column_enum_contains_all_qualified_columns(self):
        enum = self.agg_items["properties"]["agg_column"]["enum"]
        for col in ALL_QUALIFIED_COLUMNS:
            self.assertIn(col, enum)

    def test_agg_column_enum_uses_qualified_format(self):
        enum = self.agg_items["properties"]["agg_column"]["enum"]
        for col in enum:
            self.assertEqual(len(col.split(".")), 3)

    def test_agg_column_enum_does_not_contain_unqualified_columns(self):
        enum = self.agg_items["properties"]["agg_column"]["enum"]
        for col in COLUMNS_EMP + COLUMNS_DEPT:
            self.assertNotIn(col, enum)

    def test_agg_description_present(self):
        self.assertIn("description", self.agg_schema)

    def test_agg_func_description_present(self):
        self.assertIn("description", self.agg_items["properties"]["agg_func"])

    def test_agg_column_description_present(self):
        self.assertIn("description", self.agg_items["properties"]["agg_column"])
