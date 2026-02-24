"""JSON export for data integration and APIs."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from src.models import AnalysisResult


class JSONExporter:
    """
    Exports AnalysisResult to JSON format.

    Features:
    - Complete hierarchical JSON structure
    - Decimal serialization
    - Optional pretty-printing
    - Schema validation
    - API-ready format

    Attributes:
        output_path: Path for JSON file
    """

    def __init__(self, output_path: str) -> None:
        """
        Initialize JSON exporter.

        Args:
            output_path: Path for output JSON file

        TODO: Validate output path
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        analysis_result: AnalysisResult,
        pretty: bool = True
    ) -> Path:
        """
        Export analysis results to JSON.

        Args:
            analysis_result: Complete analysis results
            pretty: Pretty-print JSON (default True)

        Returns:
            Path: Path to generated JSON file

        Raises:
            IOError: If file write fails

        TODO: Serialize AnalysisResult to JSON
        TODO: Handle Decimal serialization
        TODO: Format with indentation if pretty
        TODO: Save and return file path
        """
        data = analysis_result.model_dump(mode='json')
        indent = 2 if pretty else None
        json_str = json.dumps(data, indent=indent, default=self._decimal_encoder)
        self.output_path.write_text(json_str, encoding='utf-8')
        return self.output_path

    @staticmethod
    def _decimal_encoder(obj):
        """
        JSON encoder for Decimal objects.

        Args:
            obj: Object to encode

        Returns:
            Encoded value for JSON serialization

        TODO: Convert Decimal to float or string
        """
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
