from pathlib import Path


class TestMySQLInfrastructure:
    def test_compose_includes_mysql_service(self):
        compose = Path("compose.yml").read_text(encoding="utf-8")
        assert "mysql:" in compose
        assert "docker-entrypoint-initdb.d/001-schema.sql" in compose
        assert "mysql://smartfashion:smartfashion@mysql:3306/smartfashion" in compose

    def test_schema_contains_required_tables(self):
        schema = Path("db/schema.sql").read_text(encoding="utf-8")
        for table in ["images", "jobs", "detections", "polygons", "embeddings"]:
            assert f"CREATE TABLE {table}" in schema

    def test_readme_documents_local_demo_database(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        assert "Local Demo Workflow" in readme
        assert "MySQL" in readme
