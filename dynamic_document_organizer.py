#!/usr/bin/env python3
"""
Dynamic Document Organizer for Senac MG Documents

Analyzes document URLs and creates folder hierarchy automatically
based on document patterns and naming conventions.

Usage: python3 dynamic_document_organizer.py
"""

import json
import re
import urllib.parse
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class DocumentInfo:
    """Information extracted from a document URL."""
    url: str
    original_path: str
    sanitized_filename: str
    main_category: str  # ATOS_DELIBERATIVOS, ATOS_NORMATIVOS, etc
    document_type: str  # RESOLUCAO, PORTARIA, etc
    year: Optional[str] = None
    number: Optional[str] = None
    description: str = ""
    target_folder_path: str = ""


class DynamicDocumentOrganizer:
    """Analyzes and organizes documents dynamically."""

    def __init__(self, urls_file: str = "senac_urls_docs.txt"):
        self.urls_file = Path(urls_file)
        self.documents: List[DocumentInfo] = []
        self.base_url = "https://www.mg.senac.br/"

        # Patterns for document analysis - improved to catch all variations
        self.doc_patterns = {
            'resolucao': re.compile(r'Resolu[çc][ãa]o\s*[-_\s]*(\d+)[-_\s]+(20\d{2}|19\d{2})', re.IGNORECASE),
            'portaria': re.compile(r'Portaria\s*[-_\s]*(\d+)[-_\s]+(20\d{2}|19\d{2})', re.IGNORECASE),
            'regimento': re.compile(r'Regimento', re.IGNORECASE),
            'instrucao': re.compile(r'Instru[çc][ãa]o\s+Normativa', re.IGNORECASE),
        }

    def load_and_analyze_urls(self) -> None:
        """Load URLs and analyze each document."""
        print(f"Loading URLs from {self.urls_file}")

        with open(self.urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"Total URLs: {len(urls)}")

        for url in urls:
            doc_info = self._analyze_document_url(url)
            if doc_info:
                self.documents.append(doc_info)

        print(f"Documents analyzed: {len(self.documents)}")

    def _analyze_document_url(self, url: str) -> Optional[DocumentInfo]:
        """Analyze single URL and extract document information."""
        if not url.startswith(self.base_url):
            return None

        # Parse URL path
        path = url[len(self.base_url):]
        path = urllib.parse.unquote(path)

        # Extract main category and filename
        parts = path.split('/')
        if len(parts) < 2:
            return None

        original_category = parts[0]
        filename = parts[-1]

        # Sanitize filename
        sanitized_filename = self._sanitize_filename(filename)

        # Determine main category
        main_category = self._categorize_main_folder(original_category)

        # Extract document type, number, and year
        doc_type, number, year = self._extract_document_details(filename)

        # Generate target folder path
        target_path = self._generate_target_path(main_category, doc_type, year)

        return DocumentInfo(
            url=url,
            original_path=path,
            sanitized_filename=sanitized_filename,
            main_category=main_category,
            document_type=doc_type,
            year=year,
            number=number,
            description=self._extract_description(filename),
            target_folder_path=target_path
        )

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove .pdf extension for processing
        name = filename.replace('.pdf', '')

        # Replace problematic characters
        replacements = {
            ' ': '_',
            'ç': 'c',
            'ã': 'a',
            'õ': 'o',
            'á': 'a',
            'é': 'e',
            'í': 'i',
            'ó': 'o',
            'ú': 'u',
            'â': 'a',
            'ê': 'e',
            'ô': 'o',
            ';': '_',
            ':': '_',
            '.': '_',
            '(': '_',
            ')': '_',
            '[': '_',
            ']': '_',
            '/': '_',
            '\\': '_',
        }

        for old, new in replacements.items():
            name = name.replace(old, new)

        # Remove multiple underscores
        while '__' in name:
            name = name.replace('__', '_')

        # Remove leading/trailing underscores
        name = name.strip('_')

        # Add .pdf back
        return f"{name}.pdf"

    def _categorize_main_folder(self, original_category: str) -> str:
        """Convert original category to standardized main folder name."""
        category_map = {
            'Atos Deliberativos': 'ATOS_DELIBERATIVOS',
            'Atos Normativos': 'ATOS_NORMATIVOS',
            'Documents': 'DOCUMENTOS_GERAIS',
        }
        return category_map.get(original_category, 'OUTROS_DOCUMENTOS')

    def _extract_document_details(self, filename: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Extract document type, number, and year from filename."""
        filename_clean = filename.replace('.pdf', '')

        # Try each pattern
        for doc_type, pattern in self.doc_patterns.items():
            match = pattern.search(filename_clean)
            if match:
                if doc_type == 'regimento':
                    return 'REGIMENTO', None, None
                elif doc_type == 'instrucao':
                    return 'INSTRUCAO_NORMATIVA', None, None
                else:
                    groups = match.groups()
                    number = groups[0] if len(groups) > 0 else None
                    year = groups[1] if len(groups) > 1 else None
                    return doc_type.upper(), number, year

        # Default classification
        return 'OUTROS_TIPOS', None, None

    def _extract_description(self, filename: str) -> str:
        """Extract meaningful description from filename."""
        # Remove extension and common prefixes
        desc = filename.replace('.pdf', '')

        # Remove document type and number patterns
        for pattern in self.doc_patterns.values():
            desc = pattern.sub('', desc)

        # Clean up
        desc = re.sub(r'^\s*[-_]+\s*', '', desc)
        desc = re.sub(r'\s*[-_]+\s*$', '', desc)

        return desc.strip()

    def _generate_target_path(self, main_category: str, doc_type: str, year: Optional[str]) -> str:
        """Generate the target folder path for a document."""
        path_parts = ["LEGISLACOES_SENAC_MG", main_category, doc_type]

        if year:
            path_parts.append(year)

        return "/".join(path_parts)

    def generate_folder_structure(self) -> Dict:
        """Generate the complete folder structure."""
        structure = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # Group documents by structure
        for doc in self.documents:
            main_cat = doc.main_category
            doc_type = doc.document_type
            year = doc.year or "SEM_ANO"

            structure[main_cat][doc_type][year].append(doc)

        return dict(structure)

    def print_hierarchy_preview(self) -> None:
        """Print a visual preview of the folder hierarchy."""
        structure = self.generate_folder_structure()

        print("\nDYNAMICALLY GENERATED FOLDER STRUCTURE:")
        print("=" * 60)
        print("LEGISLACOES_SENAC_MG/")

        for main_cat, doc_types in structure.items():
            print(f"├── {main_cat}/")

            doc_type_items = list(doc_types.items())
            for i, (doc_type, years) in enumerate(doc_type_items):
                is_last_type = i == len(doc_type_items) - 1
                type_prefix = "└──" if is_last_type else "├──"

                total_docs = sum(len(docs) for docs in years.values())
                print(f"│   {type_prefix} {doc_type}/ ({total_docs} documents)")

                # Show years
                year_items = list(years.items())
                for j, (year, docs) in enumerate(year_items):
                    is_last_year = j == len(year_items) - 1

                    if is_last_type:
                        year_prefix = "    └──" if is_last_year else "    ├──"
                    else:
                        year_prefix = "│   └──" if is_last_year else "│   ├──"

                    print(f"│   {year_prefix} {year}/ ({len(docs)} documents)")

    def generate_migration_config(self) -> Dict:
        """Generate configuration for the migration system."""
        structure = self.generate_folder_structure()

        config = {
            "root_folder": "LEGISLACOES_SENAC_MG",
            "total_documents": len(self.documents),
            "folder_structure": {},
            "document_mapping": [],
            "statistics": self._generate_statistics()
        }

        # Convert structure to config format
        for main_cat, doc_types in structure.items():
            config["folder_structure"][main_cat] = {}

            for doc_type, years in doc_types.items():
                config["folder_structure"][main_cat][doc_type] = {
                    "total_documents": sum(len(docs) for docs in years.values()),
                    "years": list(years.keys()),
                    "organize_by_year": len(years) > 1
                }

        # Create document mapping for migration
        for doc in self.documents:
            config["document_mapping"].append({
                "source_url": doc.url,
                "target_folder": doc.target_folder_path,
                "filename": doc.sanitized_filename,
                "document_type": doc.document_type,
                "year": doc.year,
                "main_category": doc.main_category
            })

        return config

    def _generate_statistics(self) -> Dict:
        """Generate detailed statistics."""
        stats = {
            "total_documents": len(self.documents),
            "by_main_category": Counter(doc.main_category for doc in self.documents),
            "by_document_type": Counter(doc.document_type for doc in self.documents),
            "by_year": Counter(doc.year for doc in self.documents if doc.year),
            "years_range": self._get_year_range()
        }
        return {k: dict(v) if isinstance(v, Counter) else v for k, v in stats.items()}

    def _get_year_range(self) -> str:
        """Get the range of years in the documents."""
        years = [int(doc.year) for doc in self.documents if doc.year and doc.year.isdigit()]
        if years:
            return f"{min(years)} - {max(years)}"
        return "Não identificado"

    def save_analysis(self, output_file: str = "document_organization_analysis.json") -> None:
        """Save the complete analysis to a JSON file."""
        config = self.generate_migration_config()

        # Add sample documents for preview
        config["sample_documents"] = [asdict(doc) for doc in self.documents[:10]]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"\nAnalysis saved to: {output_file}")

    def run_analysis(self) -> None:
        """Run the complete analysis process."""
        print("SENAC MG DYNAMIC DOCUMENT ANALYSIS")
        print("=" * 60)

        try:
            # Load and analyze documents
            self.load_and_analyze_urls()

            # Show preview
            self.print_hierarchy_preview()

            # Show statistics
            stats = self._generate_statistics()
            print(f"\nSTATISTICS:")
            print(f"Total documents: {stats['total_documents']}")
            print(f"Main categories: {len(stats['by_main_category'])}")
            print(f"Document types: {len(stats['by_document_type'])}")
            print(f"Period: {stats['years_range']}")

            print("\nDISTRIBUTION BY CATEGORY:")
            for category, count in stats['by_main_category'].items():
                print(f"  • {category}: {count} documents")

            print("\nDISTRIBUTION BY TYPE:")
            for doc_type, count in stats['by_document_type'].items():
                print(f"  • {doc_type}: {count} documents")

            # Save analysis
            self.save_analysis()

            print("\nANALYSIS COMPLETED SUCCESSFULLY!")
            print("Next steps:")
            print("  1. Review the 'document_organization_analysis.json' file")
            print("  2. Run the migration script with the generated structure")

        except Exception as e:
            print(f"❌ Erro durante análise: {e}")
            raise


def main():
    """Main execution function."""
    organizer = DynamicDocumentOrganizer()
    organizer.run_analysis()


if __name__ == "__main__":
    main()