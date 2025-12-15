"""DeepL Translation MCP Server.

Provides translation capabilities using the DeepL API through MCP protocol.
"""

import os
import logging
from typing import Any

import deepl
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("deepl-mcp")

# DeepL client (initialized lazily)
_translator: deepl.Translator | None = None


def get_translator() -> deepl.Translator:
    """Get or create DeepL translator instance."""
    global _translator
    if _translator is None:
        api_key = os.environ.get("DEEPL_API_KEY")
        if not api_key:
            raise ValueError(
                "DEEPL_API_KEY environment variable is not set. "
                "Please set it with your DeepL API key."
            )
        _translator = deepl.Translator(api_key)
    return _translator


# Language code mappings for common names
LANGUAGE_ALIASES: dict[str, str] = {
    # Target languages
    "english": "EN-US",
    "british english": "EN-GB",
    "american english": "EN-US",
    "japanese": "JA",
    "german": "DE",
    "french": "FR",
    "spanish": "ES",
    "italian": "IT",
    "dutch": "NL",
    "polish": "PL",
    "portuguese": "PT-PT",
    "brazilian portuguese": "PT-BR",
    "russian": "RU",
    "chinese": "ZH-HANS",
    "simplified chinese": "ZH-HANS",
    "traditional chinese": "ZH-HANT",
    "korean": "KO",
    "indonesian": "ID",
    "turkish": "TR",
    "ukrainian": "UK",
    "czech": "CS",
    "danish": "DA",
    "finnish": "FI",
    "greek": "EL",
    "hungarian": "HU",
    "norwegian": "NB",
    "romanian": "RO",
    "slovak": "SK",
    "swedish": "SV",
    "bulgarian": "BG",
    "estonian": "ET",
    "latvian": "LV",
    "lithuanian": "LT",
    "slovenian": "SL",
}


def resolve_language_code(lang: str, for_source: bool = False) -> str:
    """Resolve language name or alias to DeepL language code.

    Args:
        lang: Language name or code
        for_source: If True, convert target-specific codes to source codes

    Returns:
        Resolved language code
    """
    # Check if it's an alias
    normalized = lang.lower().strip()
    if normalized in LANGUAGE_ALIASES:
        code = LANGUAGE_ALIASES[normalized]
    else:
        code = lang.upper().strip()

    # For source language, DeepL uses simple codes (EN, not EN-US)
    if for_source and "-" in code:
        code = code.split("-")[0]

    return code


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available translation tools."""
    return [
        Tool(
            name="translate",
            description=(
                "Translate text using DeepL API. "
                "Supports 30+ languages with high-quality neural machine translation. "
                "You can use language names (e.g., 'Japanese', 'English') or "
                "language codes (e.g., 'JA', 'EN-US')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to translate",
                    },
                    "target_lang": {
                        "type": "string",
                        "description": (
                            "Target language. Examples: 'Japanese', 'JA', "
                            "'English', 'EN-US', 'German', 'DE'"
                        ),
                    },
                    "source_lang": {
                        "type": "string",
                        "description": (
                            "Source language (optional, auto-detected if not specified). "
                            "Examples: 'English', 'EN', 'Japanese', 'JA'"
                        ),
                    },
                    "formality": {
                        "type": "string",
                        "enum": ["default", "more", "less", "prefer_more", "prefer_less"],
                        "description": (
                            "Formality level (optional). "
                            "'more' for formal, 'less' for informal. "
                            "'prefer_more'/'prefer_less' are softer preferences. "
                            "Not all languages support formality."
                        ),
                    },
                    "preserve_formatting": {
                        "type": "boolean",
                        "description": (
                            "Whether to preserve formatting (optional, default: true)"
                        ),
                    },
                },
                "required": ["text", "target_lang"],
            },
        ),
        Tool(
            name="get_supported_languages",
            description=(
                "Get list of languages supported by DeepL for translation. "
                "Returns both source and target languages with their codes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["source", "target", "both"],
                        "description": (
                            "Type of languages to retrieve. "
                            "'source' for languages you can translate from, "
                            "'target' for languages you can translate to, "
                            "'both' for all (default: 'both')"
                        ),
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_usage",
            description=(
                "Get DeepL API usage statistics. "
                "Shows character count and limits for your API plan."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="detect_language",
            description=(
                "Detect the language of the given text using DeepL. "
                "Useful when you need to know the source language before translation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to detect language for",
                    },
                },
                "required": ["text"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a translation tool."""
    try:
        translator = get_translator()

        if name == "translate":
            return await handle_translate(translator, arguments)
        elif name == "get_supported_languages":
            return await handle_get_languages(translator, arguments)
        elif name == "get_usage":
            return await handle_get_usage(translator)
        elif name == "detect_language":
            return await handle_detect_language(translator, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except deepl.DeepLException as e:
        logger.error(f"DeepL API error: {e}")
        return [TextContent(type="text", text=f"DeepL API error: {str(e)}")]
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def handle_translate(
    translator: deepl.Translator, arguments: dict[str, Any]
) -> list[TextContent]:
    """Handle translation request."""
    text = arguments.get("text", "")
    if not text:
        return [TextContent(type="text", text="Error: 'text' parameter is required")]

    target_lang = arguments.get("target_lang", "")
    if not target_lang:
        return [TextContent(type="text", text="Error: 'target_lang' parameter is required")]

    # Resolve language codes
    target_lang = resolve_language_code(target_lang, for_source=False)

    source_lang = arguments.get("source_lang")
    if source_lang:
        source_lang = resolve_language_code(source_lang, for_source=True)

    # Build translation options
    options: dict[str, Any] = {
        "text": text,
        "target_lang": target_lang,
    }

    if source_lang:
        options["source_lang"] = source_lang

    formality = arguments.get("formality")
    if formality and formality != "default":
        options["formality"] = formality

    preserve_formatting = arguments.get("preserve_formatting", True)
    options["preserve_formatting"] = preserve_formatting

    # Perform translation
    result = translator.translate_text(**options)

    # Format response
    detected_source = result.detected_source_lang if hasattr(result, 'detected_source_lang') else "unknown"

    response_lines = [
        f"**Translated Text:**",
        "",
        result.text,
        "",
        "---",
        f"*Source language: {detected_source}*",
        f"*Target language: {target_lang}*",
    ]

    return [TextContent(type="text", text="\n".join(response_lines))]


async def handle_get_languages(
    translator: deepl.Translator, arguments: dict[str, Any]
) -> list[TextContent]:
    """Handle get supported languages request."""
    lang_type = arguments.get("type", "both")

    lines = []

    if lang_type in ("source", "both"):
        source_langs = translator.get_source_languages()
        lines.append("## Source Languages (translate from)")
        lines.append("")
        for lang in sorted(source_langs, key=lambda x: x.name):
            lines.append(f"- **{lang.name}** (`{lang.code}`)")
        lines.append("")

    if lang_type in ("target", "both"):
        target_langs = translator.get_target_languages()
        lines.append("## Target Languages (translate to)")
        lines.append("")
        for lang in sorted(target_langs, key=lambda x: x.name):
            formality_info = ""
            if hasattr(lang, 'supports_formality') and lang.supports_formality:
                formality_info = " - supports formality"
            lines.append(f"- **{lang.name}** (`{lang.code}`){formality_info}")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_usage(translator: deepl.Translator) -> list[TextContent]:
    """Handle get usage request."""
    usage = translator.get_usage()

    lines = ["## DeepL API Usage", ""]

    if usage.character:
        count = usage.character.count
        limit = usage.character.limit
        percentage = (count / limit * 100) if limit else 0
        remaining = limit - count if limit else "unlimited"

        lines.extend([
            f"**Characters Used:** {count:,}",
            f"**Character Limit:** {limit:,}" if limit else "**Character Limit:** Unlimited",
            f"**Remaining:** {remaining:,}" if isinstance(remaining, int) else f"**Remaining:** {remaining}",
            f"**Usage:** {percentage:.1f}%",
        ])

    if usage.document:
        lines.extend([
            "",
            "### Document Translation",
            f"**Documents Used:** {usage.document.count:,}",
            f"**Document Limit:** {usage.document.limit:,}" if usage.document.limit else "**Document Limit:** Unlimited",
        ])

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_detect_language(
    translator: deepl.Translator, arguments: dict[str, Any]
) -> list[TextContent]:
    """Handle language detection request."""
    text = arguments.get("text", "")
    if not text:
        return [TextContent(type="text", text="Error: 'text' parameter is required")]

    # DeepL doesn't have a dedicated detect endpoint, so we translate to a dummy target
    # and get the detected source language
    result = translator.translate_text(text, target_lang="EN-US")
    detected = result.detected_source_lang

    # Get language name
    source_langs = translator.get_source_languages()
    lang_name = detected
    for lang in source_langs:
        if lang.code.upper() == detected.upper():
            lang_name = lang.name
            break

    lines = [
        f"**Detected Language:** {lang_name} (`{detected}`)",
        "",
        f"*Text analyzed: \"{text[:100]}{'...' if len(text) > 100 else ''}\"*",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


def main() -> None:
    """Main entry point for the MCP server."""
    import asyncio

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
