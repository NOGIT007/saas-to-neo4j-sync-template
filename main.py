"""
{PROJECT_NAME} FastMCP Server
==============================
MCP server exposing Neo4j operations to Claude AI via Model Context Protocol.

This server provides tools for:
- Querying the {PROJECT_NAME} knowledge graph
- Executing Cypher queries
- Getting dashboard metrics
- Retrieving entity details
- Analyzing relationships

Requirements:
    - Neo4j database with synced {PROJECT_NAME} data
    - Environment variables configured (see .env.example)

Usage:
    # Local testing with FastMCP CLI
    fastmcp dev main.py

    # Deploy to FastMCP Cloud
    # The variable MUST be named 'app' for deployment

TODO: Customize tools for your specific graph schema
"""

import os
import logging
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from neo4j import AsyncGraphDatabase, AsyncDriver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CRITICAL: Variable must be named 'app' for FastMCP Cloud deployment
app = FastMCP("{project}-database")

# Environment configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Global driver with lazy initialization
driver: Optional[AsyncDriver] = None


async def get_driver() -> AsyncDriver:
    """Get or create Neo4j async driver"""
    global driver
    if driver is None:
        driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        await driver.verify_connectivity()
        logger.info("Connected to Neo4j")
    return driver


def serialize_neo4j_value(value: Any) -> Any:
    """Convert Neo4j objects to JSON-safe Python types"""
    from neo4j.graph import Node, Relationship, Path
    from neo4j.time import DateTime, Date, Time

    if isinstance(value, Node):
        return {
            "id": value.element_id,
            "labels": list(value.labels),
            "properties": {k: serialize_neo4j_value(v) for k, v in value.items()}
        }
    elif isinstance(value, Relationship):
        return {
            "id": value.element_id,
            "type": value.type,
            "start": value.start_node.element_id,
            "end": value.end_node.element_id,
            "properties": {k: serialize_neo4j_value(v) for k, v in value.items()}
        }
    elif isinstance(value, Path):
        return {
            "nodes": [serialize_neo4j_value(n) for n in value.nodes],
            "relationships": [serialize_neo4j_value(r) for r in value.relationships]
        }
    elif isinstance(value, (DateTime, Date, Time)):
        return value.isoformat()
    elif isinstance(value, dict):
        return {k: serialize_neo4j_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [serialize_neo4j_value(item) for item in value]
    else:
        return value


# =============================================================================
# READ TOOLS - General Query Operations
# =============================================================================

@app.tool()
async def execute_cypher(query: str, parameters: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict:
    """
    Execute a Cypher query against the Neo4j database.

    Args:
        query: Cypher query string
        parameters: Optional query parameters as dictionary
        timeout: Query timeout in seconds (default: 30)

    Returns:
        Dictionary with results and metadata
    """
    try:
        driver = await get_driver()
        async with driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            summary = await result.consume()

            return {
                "success": True,
                "records": [serialize_neo4j_value(r) for r in records],
                "count": len(records),
                "summary": {
                    "query_type": summary.query_type,
                    "counters": dict(summary.counters)
                }
            }
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.tool()
async def get_schema() -> Dict:
    """
    Get comprehensive graph schema information.

    Returns:
        Dictionary with node labels, relationship types, and property keys
    """
    try:
        driver = await get_driver()
        async with driver.session(database=NEO4J_DATABASE) as session:
            # Get all node labels
            labels_result = await session.run("CALL db.labels()")
            labels = [record["label"] async for record in labels_result]

            # Get all relationship types
            rels_result = await session.run("CALL db.relationshipTypes()")
            relationship_types = [record["relationshipType"] async for record in rels_result]

            # Get all property keys
            props_result = await session.run("CALL db.propertyKeys()")
            property_keys = [record["propertyKey"] async for record in props_result]

            return {
                "success": True,
                "node_labels": labels,
                "relationship_types": relationship_types,
                "property_keys": property_keys
            }
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# TODO: Add your custom tools here
# =============================================================================

# Examples of custom tools you might want to add:
# - get_dashboard_metrics() - Top-level KPIs
# - get_{entity}_list() - List entities with filters
# - get_{entity}_detail() - Single entity details
# - get_{entity}_relationships() - Entity relationships
# - find_paths() - Path finding between entities
# - search_{entity}() - Search entities by properties

# TODO: Implement custom tools following this pattern:
#
# @app.tool()
# async def get_dashboard_metrics(filters: Optional[Dict] = None) -> Dict:
#     """
#     Get dashboard KPIs for {PROJECT_NAME}.
#
#     Args:
#         filters: Optional filters dict
#
#     Returns:
#         Dictionary with dashboard metrics
#     """
#     query = """
#     // TODO: Write your Cypher query here
#     MATCH (n:YourEntity)
#     RETURN count(n) as total
#     """
#     return await execute_cypher(query)


# =============================================================================
# LIFECYCLE HOOKS
# =============================================================================

@app.on_startup()
async def startup():
    """Initialize on server startup"""
    await get_driver()
    logger.info("{PROJECT_NAME} MCP server started")


@app.on_shutdown()
async def shutdown():
    """Cleanup on server shutdown"""
    global driver
    if driver:
        await driver.close()
        logger.info("Neo4j connection closed")
