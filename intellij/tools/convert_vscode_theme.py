#!/usr/bin/env python3
"""Convert the Orchids VS Code themes to IntelliJ themes.

Usage:
    python3 intellij/tools/convert_vscode_theme.py

Reads  vscode/themes/orchids-{dark,light}-color-theme.json
Writes intellij/themes/Orchids-{Dark,Light}.icls
      intellij/themes/Orchids-{Dark,Light}.theme.json
      intellij/themes/Orchids-Islands-{Dark,Light}.theme.json
      intellij/plugin/                      (JetBrains theme plugin package)
      intellij/dist/Orchids-IntelliJ-Plugin.zip
"""

import json
import os
import re
import zipfile
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VSCODE_THEMES = os.path.join(ROOT, "vscode", "themes")
INTELLIJ_THEMES_DIR = os.path.join(ROOT, "intellij", "themes")
PLUGIN_DIR = os.path.join(ROOT, "intellij", "plugin")
PLUGIN_THEMES_DIR = os.path.join(PLUGIN_DIR, "themes")
PLUGIN_META_DIR = os.path.join(PLUGIN_DIR, "META-INF")
DIST_DIR = os.path.join(ROOT, "intellij", "dist")
PLUGIN_ZIP = os.path.join(DIST_DIR, "Orchids-IntelliJ-Plugin.zip")

PLUGIN_ID = "com.github.mattegrant.orchids"
PLUGIN_NAME = "Orchids Theme"
PLUGIN_VENDOR = "Matteo Guadrini"
PLUGIN_VENDOR_URL = "https://github.com/MatteoGuadrini/orchids"
PLUGIN_SINCE_BUILD = "231"
PLUGIN_VERSION = "0.1.0"

VERSION = "142"

UI_THEME_SPECS = [
    {
        "source": "orchids-dark-color-theme.json",
        "variant": "new",
        "name": "Orchids Dark",
        "file": "Orchids-Dark.theme.json",
        "parent_theme": "ExperimentalDark",
        "target_ui": "new",
        "provider_key": "dark.new",
    },
    {
        "source": "orchids-light-color-theme.json",
        "variant": "new",
        "name": "Orchids Light",
        "file": "Orchids-Light.theme.json",
        "parent_theme": "ExperimentalLight",
        "target_ui": "new",
        "provider_key": "light.new",
    },
    {
        "source": "orchids-dark-color-theme.json",
        "variant": "islands",
        "name": "Orchids Islands Dark",
        "file": "Orchids-Islands-Dark.theme.json",
        "parent_theme": "Islands Dark",
        "target_ui": "islands",
        "provider_key": "dark.islands",
    },
    {
        "source": "orchids-light-color-theme.json",
        "variant": "islands",
        "name": "Orchids Islands Light",
        "file": "Orchids-Islands-Light.theme.json",
        "parent_theme": "Islands Light",
        "target_ui": "islands",
        "provider_key": "light.islands",
    },
]

THEMES = [
    ("orchids-dark-color-theme.json", "Darcula", "Orchids-Dark.icls"),
    ("orchids-light-color-theme.json", "Default", "Orchids-Light.icls"),
]


def parse_color(value):
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if not value.startswith("#"):
        return None
    value = value[1:]
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) == 6:
        value += "ff"
    if len(value) != 8 or not re.fullmatch(r"[0-9a-fA-F]{8}", value):
        return None
    return tuple(int(value[i:i + 2], 16) for i in range(0, 8, 2))


def composite(fg, bg):
    alpha = fg[3] / 255.0
    return tuple(round(fg[i] * alpha + bg[i] * (1 - alpha)) for i in range(3))


def color_hex(value, background=None):
    parsed = parse_color(value)
    if parsed is None:
        return None
    if parsed[3] < 255 and background is not None:
        parsed = composite(parsed, background) + (255,)
    return "%02X%02X%02X" % parsed[:3]


def first_color(colors, *keys):
    for key in keys:
        value = colors.get(key)
        if value:
            return value
    return None


def font_bits(font_style):
    if not font_style:
        return 0
    bits = 0
    if "bold" in font_style:
        bits |= 1
    if "italic" in font_style:
        bits |= 2
    return bits


def scope_selectors(token_color):
    scope = token_color.get("scope")
    if scope is None:
        return []
    if isinstance(scope, str):
        scope = [scope]
    selectors = []
    for item in scope:
        if isinstance(item, str):
            selectors.extend(part.strip() for part in item.split(",") if part.strip())
    return selectors


def token_rules(theme):
    return [
        (scope_selectors(token), token.get("settings", {}), index)
        for index, token in enumerate(theme.get("tokenColors", []))
    ]


def resolve_scope(rules, query):
    best = None
    for selectors, settings, index in rules:
        for selector in selectors:
            if query == selector or query.startswith(selector + "."):
                score = (len(selector.split(".")), len(selector), index)
                if best is None or score > best[0]:
                    best = (score, settings)
    return best[1] if best else {}


def attribute_xml(name, foreground=None, background=None, font_type=0,
                  effect_type=None, effect_color=None, error_stripe=None):
    parts = []
    if foreground:
        parts.append(f'        <option name="FOREGROUND" value="{foreground}" />\n')
    if background:
        parts.append(f'        <option name="BACKGROUND" value="{background}" />\n')
    if font_type:
        parts.append(f'        <option name="FONT_TYPE" value="{font_type}" />\n')
    if effect_type is not None:
        parts.append(f'        <option name="EFFECT_TYPE" value="{effect_type}" />\n')
    if effect_color:
        parts.append(f'        <option name="EFFECT_COLOR" value="{effect_color}" />\n')
    if error_stripe:
        parts.append(f'        <option name="ERROR_STRIPE_COLOR" value="{error_stripe}" />\n')
    if not parts:
        return None
    return (
        f'    <option name="{escape(name)}">\n'
        '      <value>\n'
        + "".join(parts)
        + '      </value>\n'
        '    </option>\n'
    )


def scoped_attribute(name, queries, rules, editor_background):
    for query in queries:
        settings = resolve_scope(rules, query)
        if not settings:
            continue
        foreground = color_hex(settings.get("foreground"))
        background = color_hex(settings.get("background"), editor_background)
        font_style = settings.get("fontStyle", "")
        font_type = font_bits(font_style)
        effect_type = effect_color = None
        if "underline" in font_style and foreground:
            effect_type = 1
            effect_color = foreground
        result = attribute_xml(name, foreground, background, font_type,
                               effect_type, effect_color)
        if result:
            return result
    return None


SCOPED_ATTRIBUTES = [
    # IntelliJ platform defaults
    ("DEFAULT_IDENTIFIER", ["variable", "identifier"]),
    ("DEFAULT_KEYWORD", ["keyword", "storage.type", "storage.modifier"]),
    ("DEFAULT_STRING", ["string"]),
    ("DEFAULT_NUMBER", ["constant.numeric", "constant.language", "number"]),
    ("DEFAULT_CONSTANT", ["constant", "variable.other.constant"]),
    ("DEFAULT_FUNCTION_DECLARATION", ["entity.name.function", "support.function", "variable.function"]),
    ("DEFAULT_FUNCTION_CALL", ["meta.function-call", "variable.function", "support.function", "entity.name.function"]),
    ("DEFAULT_INSTANCE_METHOD", ["meta.method", "storage.type.method", "entity.name.function", "support.function"]),
    ("DEFAULT_STATIC_METHOD", ["meta.method", "storage.type.method", "entity.name.function", "support.function"]),
    ("DEFAULT_PARAMETER", ["variable.parameter"]),
    ("DEFAULT_REASSIGNED_PARAMETER", ["variable.parameter"]),
    ("DEFAULT_LOCAL_VARIABLE", ["variable.other", "variable"]),
    ("DEFAULT_REASSIGNED_LOCAL_VARIABLE", ["variable.other", "variable"]),
    ("DEFAULT_GLOBAL_VARIABLE", ["variable.other", "variable"]),
    ("DEFAULT_INSTANCE_FIELD", ["variable.other.field", "variable.other", "variable"]),
    ("DEFAULT_STATIC_FIELD", ["variable.other.constant", "variable.other.field", "variable.other", "constant"]),
    ("DEFAULT_CLASS_NAME", ["entity.name.class", "entity.name.type", "support.class", "support.type"]),
    ("DEFAULT_INTERFACE_NAME", ["entity.name.interface", "entity.name.type", "support.type"]),
    ("DEFAULT_CLASS_REFERENCE", ["entity.name.type", "support.type", "support.class"]),
    ("DEFAULT_OPERATION_SIGN", ["keyword.operator"]),
    ("DEFAULT_BRACES", ["meta.brace", "punctuation"]),
    ("DEFAULT_BRACKETS", ["punctuation.section", "meta.brace", "punctuation"]),
    ("DEFAULT_PARENTHS", ["meta.brace", "punctuation"]),
    ("DEFAULT_COMMA", ["punctuation.separator", "punctuation"]),
    ("DEFAULT_SEMICOLON", ["punctuation.terminator", "punctuation.separator", "punctuation"]),
    ("DEFAULT_DOT", ["punctuation.accessor", "punctuation"]),
    ("DEFAULT_LINE_COMMENT", ["comment.line", "comment"]),
    ("DEFAULT_BLOCK_COMMENT", ["comment.block", "comment"]),
    ("DEFAULT_DOC_COMMENT", ["comment.block.documentation", "comment.line.documentation", "comment.block", "comment"]),
    ("DEFAULT_DOC_MARKUP", ["comment.block.documentation", "markup", "comment"]),
    ("DEFAULT_DOC_COMMENT_TAG", ["comment.block.documentation", "storage.type", "comment"]),
    ("DEFAULT_DOC_COMMENT_TAG_VALUE", ["comment.block.documentation", "string", "comment"]),
    ("DOC_CODE_INLINE", ["markup.raw.inline", "markup.code", "string"]),
    ("DOC_CODE_BLOCK", ["markup.fenced_code.block", "markup.code", "string"]),
    ("DEFAULT_VALID_STRING_ESCAPE", ["constant.character.escape", "constant.character", "string.escape"]),
    ("DEFAULT_INVALID_STRING_ESCAPE", ["invalid", "constant.character.escape"]),
    ("DEFAULT_METADATA", ["meta.decorator", "decorator", "annotation", "meta.annotation", "meta.attribute"]),
    ("DEFAULT_ATTRIBUTE", ["entity.other.attribute-name", "meta.attribute", "meta.annotation", "attribute", "annotation"]),
    ("DEFAULT_TAG", ["entity.name.tag", "meta.tag", "tag"]),
    ("DEFAULT_ENTITY", ["constant.character.entity", "entity.other.attribute-name"]),
    ("MARKUP_TAG", ["entity.name.tag", "meta.tag", "tag"]),
    ("MARKUP_ATTRIBUTE", ["entity.other.attribute-name", "meta.attribute", "meta.annotation", "attribute"]),
    ("MARKUP_ENTITY", ["constant.character.entity"]),
    ("DEFAULT_LABEL", ["entity.name.label", "label"]),
    ("LABEL", ["entity.name.label", "label"]),
    ("DEFAULT_PREDEFINED_SYMBOL", ["constant.language", "variable.language", "constant"]),
    ("DEFAULT_HIGHLIGHTED_REFERENCE", ["variable", "identifier"]),
    ("DEFAULT_TEMPLATE_LANGUAGE_COLOR", ["variable", "identifier"]),
    ("ENUM_CONST", ["constant", "variable.other.constant"]),
    ("TYPEDEF", ["entity.name.type", "support.type", "keyword.type"]),

    # Legacy/default attribute aliases used by older JetBrains schemes
    ("CLASS_NAME_ATTRIBUTES", ["entity.name.class", "entity.name.type", "support.class", "support.type"]),
    ("INSTANCE_FIELD_ATTRIBUTES", ["variable.other.field", "variable.other", "variable"]),
    ("STATIC_FIELD_ATTRIBUTES", ["variable.other.constant", "variable.other.field", "variable.other", "constant"]),
    ("LOCAL_VARIABLE_ATTRIBUTES", ["variable.other", "variable"]),
    ("PARAMETER_ATTRIBUTES", ["variable.parameter"]),
    ("STATIC_METHOD_ATTRIBUTES", ["meta.method", "storage.type.method", "entity.name.function", "support.function"]),

    # Java
    ("JAVA_KEYWORD", ["keyword", "storage.type"]),
    ("JAVA_STRING", ["string"]),
    ("JAVA_NUMBER", ["constant.numeric", "constant.language"]),
    ("JAVA_OPERATION_SIGN", ["keyword.operator"]),
    ("JAVA_LINE_COMMENT", ["comment.line", "comment"]),
    ("JAVA_BLOCK_COMMENT", ["comment.block", "comment"]),
    ("JAVA_DOC_COMMENT", ["comment.block.documentation", "comment.block", "comment"]),
    ("JAVA_DOC_MARKUP", ["comment.block.documentation", "comment"]),
    ("JAVA_DOC_TAG", ["comment.block.documentation", "storage.type", "comment"]),
    ("JAVA_VALID_STRING_ESCAPE", ["constant.character.escape", "constant.character"]),
    ("JAVA_INVALID_STRING_ESCAPE", ["invalid", "constant.character.escape"]),
    ("JAVA_BRACES", ["meta.brace", "punctuation"]),
    ("JAVA_BRACKETS", ["punctuation.section", "meta.brace", "punctuation"]),
    ("JAVA_COMMA", ["punctuation.separator", "punctuation"]),
    ("JAVA_DOT", ["punctuation.accessor", "punctuation"]),
    ("JAVA_PARENTH", ["meta.brace", "punctuation"]),
    ("JAVA_SEMICOLON", ["punctuation.terminator", "punctuation.separator", "punctuation"]),

    # Python
    ("PY.KEYWORD", ["keyword", "storage.type"]),
    ("PY.STRING", ["string"]),
    ("PY.NUMBER", ["constant.numeric", "constant.language"]),
    ("PY.OPERATION_SIGN", ["keyword.operator"]),
    ("PY.LINE_COMMENT", ["comment.line", "comment"]),
    ("PY.BLOCK_COMMENT", ["comment.block", "comment"]),
    ("PY.DOC_COMMENT", ["comment.block.documentation", "comment.block", "comment"]),
    ("PY.CLASS_DEFINITION", ["entity.name.class", "entity.name.type", "support.class"]),
    ("PY.FUNC_DEFINITION", ["entity.name.function", "support.function"]),
    ("PY.DECORATOR", ["meta.decorator.python", "punctuation.decorator.python", "meta.decorator", "decorator", "annotation"]),
    ("PY.PREDEFINED_DEFINITION", ["support.function", "variable.language", "constant.language"]),
    ("PY.PREDEFINED_USAGE", ["support.function", "variable.language", "constant.language"]),
    ("PY.BUILTIN_NAME", ["support.function", "variable.language", "constant.language"]),
    ("PY.VALID_STRING_ESCAPE", ["constant.character.escape", "constant.character"]),
    ("PY.INVALID_STRING_ESCAPE", ["invalid", "constant.character.escape"]),
    ("PY.BRACES", ["meta.brace", "punctuation"]),
    ("PY.BRACKETS", ["punctuation.section", "meta.brace", "punctuation"]),
    ("PY.COMMA", ["punctuation.separator", "punctuation"]),
    ("PY.DOT", ["punctuation.accessor", "punctuation"]),
    ("PY.PARENTHS", ["meta.brace", "punctuation"]),
    ("PY.SEMICOLON", ["punctuation.terminator", "punctuation.separator", "punctuation"]),

    # JavaScript / TypeScript
    ("JS.GLOBAL_VARIABLE", ["variable.other", "variable"]),
    ("JS.LOCAL_VARIABLE", ["variable.other", "variable"]),
    ("JS.PARAMETER", ["variable.parameter"]),
    ("JS.INSTANCE_MEMBER_FUNCTION", ["meta.method", "entity.name.function", "support.function"]),
    ("JS.REGEXP", ["string.regexp", "string"]),

    # CSS / Sass / Less
    ("CSS.COMMENT", ["comment", "comment.line", "comment.block"]),
    ("CSS.FUNCTION", ["support.function", "entity.name.function"]),
    ("CSS.IDENT", ["variable", "identifier"]),
    ("CSS.NUMBER", ["constant.numeric", "constant.language"]),
    ("CSS.PROPERTY_NAME", ["support.type.property-name", "entity.other.attribute-name", "key"]),
    ("CSS.PROPERTY_VALUE", ["support.constant.property-value", "support.constant", "constant.other.color", "string"]),
    ("CSS.TAG_NAME", ["entity.name.tag", "entity.other.attribute-name.tag", "meta.tag"]),
    ("CSS.URL", ["markup.underline.link", "string.other.link", "string", "support.constant", "constant.other.symbol"]),
    ("SASS_COMMENT", ["comment", "comment.line", "comment.block"]),
    ("SASS_DEFAULT", ["variable", "identifier"]),
    ("SASS_EXTEND", ["keyword", "keyword.control"]),
    ("SASS_FUNCTION", ["support.function", "entity.name.function"]),
    ("SASS_IDENTIFIER", ["variable", "identifier"]),
    ("SASS_IMPORTANT", ["keyword", "keyword.control", "storage.modifier"]),
    ("SASS_KEYWORD", ["keyword", "storage.type"]),
    ("SASS_MIXIN", ["support.function", "entity.name.function", "meta.function-call"]),
    ("SASS_NUMBER", ["constant.numeric", "constant.language"]),
    ("SASS_PROPERTY_NAME", ["support.type.property-name", "entity.other.attribute-name", "key"]),
    ("SASS_PROPERTY_VALUE", ["support.constant.property-value", "support.constant", "constant.other.color", "string"]),
    ("SASS_STRING", ["string"]),
    ("SASS_TAG_NAME", ["entity.name.tag", "entity.other.attribute-name.tag", "meta.tag"]),
    ("SASS_URL", ["markup.underline.link", "string.other.link", "string", "support.constant", "constant.other.symbol"]),
    ("SASS_VARIABLE", ["variable", "identifier"]),
    ("LESS_VARIABLE", ["variable", "variable.other", "identifier"]),
    ("LESS_INJECTED_CODE", ["variable", "identifier"]),
    ("LESS_JS_CODE_DELIM", ["punctuation", "keyword.operator"]),

    # HTML / XML
    ("HTML_TAG_NAME", ["entity.name.tag", "meta.tag", "tag"]),
    ("HTML_ATTRIBUTE_NAME", ["entity.other.attribute-name", "meta.attribute", "attribute"]),
    ("HTML_ATTRIBUTE_VALUE", ["string", "support.constant.property-value"]),
    ("HTML_COMMENT", ["comment", "comment.block", "comment.line"]),
    ("HTML_ENTITY_REFERENCE", ["constant.character.entity"]),
    ("XML_TAG", ["entity.name.tag", "meta.tag", "tag"]),
    ("XML_TAG_NAME", ["entity.name.tag", "meta.tag", "tag"]),
    ("XML_TAG_DATA", ["variable", "identifier"]),
    ("XML_ATTRIBUTE_NAME", ["entity.other.attribute-name", "meta.attribute", "attribute"]),
    ("XML_ATTRIBUTE_VALUE", ["string", "support.constant.property-value"]),
    ("XML_ENTITY_REFERENCE", ["constant.character.entity"]),
    ("XML_PROLOGUE", ["meta.preprocessor", "keyword.control.directive", "keyword"]),

    # YAML
    ("YAML_COMMENT", ["comment", "comment.line", "comment.block"]),
    ("YAML_SCALAR_KEY", ["entity.name.tag.yaml", "entity.other.attribute-name", "key"]),
    ("YAML_SCALAR_VALUE", ["string", "support.constant", "constant.numeric"]),
    ("YAML_SCALAR_STRING", ["string"]),
    ("YAML_SCALAR_DSTRING", ["string"]),
    ("YAML_SIGN", ["keyword", "entity.name.tag.yaml", "entity.other.attribute-name"]),
    ("YAML_TEXT", ["variable", "identifier"]),

    # PHP
    ("PHP_VAR", ["variable.other.php", "variable.other", "variable"]),
    ("PHP_PARAMETER", ["variable.parameter"]),

    # Ruby
    ("RUBY_BAD_CHARACTER", ["invalid", "invalid.illegal"]),
    ("RUBY_BRACKETS", ["meta.brace", "punctuation"]),
    ("RUBY_COLON", ["punctuation.separator", "punctuation.terminator", "punctuation"]),
    ("RUBY_COMMA", ["punctuation.separator", "punctuation"]),
    ("RUBY_COMMENT", ["comment", "comment.line", "comment.block"]),
    ("RUBY_CONSTANT", ["constant", "variable.other.constant"]),
    ("RUBY_CONSTANT_DECLARATION", ["constant", "variable.other.constant"]),
    ("RUBY_CVAR", ["variable.other", "variable"]),
    ("RUBY_DOT", ["punctuation.accessor", "punctuation"]),
    ("RUBY_ESCAPE_SEQUENCE", ["constant.character.escape", "constant.character"]),
    ("RUBY_EXPR_IN_STRING", ["string", "variable"]),
    ("RUBY_GVAR", ["variable.other.readwrite.global", "variable.other", "variable"]),
    ("RUBY_HASH_ASSOC", ["variable.other.property", "variable.other", "variable"]),
    ("RUBY_HEREDOC_CONTENT", ["string"]),
    ("RUBY_HEREDOC_ID", ["string"]),
    ("RUBY_IDENTIFIER", ["variable", "identifier"]),
    ("RUBY_INTERPOLATED_STRING", ["string"]),
    ("RUBY_INVALID_ESCAPE_SEQUENCE", ["invalid", "constant.character.escape"]),
    ("RUBY_IVAR", ["variable.other", "variable"]),
    ("RUBY_KEYWORD", ["keyword", "storage.type"]),
    ("RUBY_LINE_CONTINUATION", ["punctuation", "keyword.operator"]),
    ("RUBY_LOCAL_VAR_ID", ["variable.other", "variable"]),
    ("RUBY_METHOD_NAME", ["entity.name.function", "support.function", "variable.function"]),
    ("RUBY_NTH_REF", ["constant.numeric", "constant.language"]),
    ("RUBY_NUMBER", ["constant.numeric", "constant.language"]),
    ("RUBY_OPERATION_SIGN", ["keyword.operator"]),
    ("RUBY_PARAMDEF_CALL", ["variable.parameter"]),
    ("RUBY_PARAMETER_ID", ["variable.parameter"]),
    ("RUBY_REGEXP", ["string.regexp", "string"]),
    ("RUBY_SEMICOLON", ["punctuation.terminator", "punctuation.separator", "punctuation"]),
    ("RUBY_SPECIFIC_CALL", ["entity.name.function", "support.function", "variable.function"]),
    ("RUBY_STRING", ["string"]),
    ("RUBY_SYMBOL", ["constant.other.symbol.ruby", "constant.other.symbol", "string"]),
    ("RUBY_WORDS", ["keyword", "storage.type"]),

    # Go
    ("GO_BLOCK_COMMENT", ["comment.block", "comment"]),
    ("GO_BUILTIN_CONSTANT", ["constant.language.go", "constant.language", "constant"]),
    ("GO_BUILTIN_FUNCTION_CALL", ["support.function.builtin.go", "support.function", "entity.name.function"]),
    ("GO_BUILTIN_TYPE_REFERENCE", ["support.type", "entity.name.type", "support.class"]),
    ("GO_BUILTIN_VARIABLE", ["variable.other", "variable"]),
    ("GO_EXPORTED_FUNCTION", ["entity.name.function", "support.function"]),
    ("GO_EXPORTED_FUNCTION_CALL", ["entity.name.function", "support.function", "meta.function-call"]),
    ("GO_KEYWORD", ["keyword", "storage.type"]),
    ("GO_LINE_COMMENT", ["comment.line", "comment"]),
    ("GO_LOCAL_CONSTANT", ["constant.language.go", "constant.language", "constant"]),
    ("GO_LOCAL_FUNCTION", ["entity.name.function", "support.function"]),
    ("GO_LOCAL_FUNCTION_CALL", ["entity.name.function", "support.function", "meta.function-call"]),
    ("GO_METHOD_RECEIVER", ["variable.parameter", "variable.other", "variable"]),
    ("GO_PACKAGE", ["support.module", "entity.name", "variable"]),
    ("GO_PACKAGE_EXPORTED_CONSTANT", ["constant.language.go", "constant.language", "constant"]),
    ("GO_PACKAGE_LOCAL_CONSTANT", ["constant.language.go", "constant.language", "constant"]),
    ("GO_TYPE_REFERENCE", ["support.type", "entity.name.type", "support.class"]),

    # Objective-C
    ("OC.BADCHARACTER", ["invalid", "invalid.illegal"]),
    ("OC.BLOCK_COMMENT", ["comment.block", "comment"]),
    ("OC.BRACES", ["meta.brace", "punctuation"]),
    ("OC.BRACKETS", ["punctuation.section", "meta.brace", "punctuation"]),
    ("OC.COMMA", ["punctuation.separator", "punctuation"]),
    ("OC.CPP_KEYWORD", ["keyword", "storage.type"]),
    ("OC.DIRECTIVE", ["meta.preprocessor", "keyword.control.directive", "keyword"]),
    ("OC.DOT", ["punctuation.accessor", "punctuation"]),
    ("OC.EXTERN_VARIABLE", ["variable.other", "variable"]),
    ("OC.GLOBAL_VARIABLE", ["variable.other", "variable"]),
    ("OC.KEYWORD", ["keyword", "storage.type"]),
    ("OC.LINE_COMMENT", ["comment.line", "comment"]),
    ("OC.LOCAL_VARIABLE", ["variable.other", "variable"]),
    ("OC.MESSAGE_ARGUMENT", ["variable.parameter", "variable.other", "variable"]),
    ("OC.METHOD_DECLARATION", ["entity.name.function", "support.function", "variable.function"]),
    ("OC.NUMBER", ["constant.numeric", "constant.language"]),
    ("OC.OPERATION_SIGN", ["keyword.operator"]),
    ("OC.PARAMETER", ["variable.parameter"]),
    ("OC.PARENTHS", ["meta.brace", "punctuation"]),
    ("OC.PROPERTY", ["variable.other.property", "variable.other", "variable"]),
    ("OC.SELFSUPERTHIS", ["variable.language", "variable.parameter.self", "variable.parameter.this"]),
    ("OC.SEMICOLON", ["punctuation.terminator", "punctuation.separator", "punctuation"]),
    ("OC.STRING", ["string"]),
    ("OC.STRUCT_FIELD", ["variable.other.field", "variable.other", "variable"]),

    # GraphQL
    ("GQL_ID", ["variable", "identifier"]),
    ("GQL_INT_LITERAL", ["constant.numeric", "constant.language"]),
    ("GQL_KEYWORD", ["keyword", "keyword.directive", "storage.type"]),
    ("GQL_STRING_LITERAL", ["string"]),

    # Cucumber / Gherkin
    ("GHERKIN_COMMENT", ["comment", "comment.line", "comment.block"]),
    ("GHERKIN_KEYWORD", ["keyword", "storage.type"]),
    ("GHERKIN_OUTLINE_PARAMETER_SUBSTITUTION", ["variable.parameter", "variable"]),
    ("GHERKIN_PYSTRING", ["string"]),
    ("GHERKIN_REGEXP_PARAMETER", ["string.regexp", "string"]),
    ("GHERKIN_TABLE_CELL", ["variable", "identifier"]),
    ("GHERKIN_TABLE_HEADER_CELL", ["entity.name.label", "entity.other.attribute-name", "keyword"]),
    ("GHERKIN_TABLE_PIPE", ["punctuation", "keyword.operator"]),
    ("GHERKIN_TAG", ["entity.name.label", "entity.other.attribute-name", "keyword"]),
    ("GHERKIN_TEXT", ["variable", "identifier"]),

    # Puppet
    ("PUPPET_BAD_CHARACTER", ["invalid", "invalid.illegal"]),
    ("PUPPET_BLOCK_COMMENT", ["comment.block", "comment"]),
    ("PUPPET_BRACES", ["meta.brace", "punctuation"]),
    ("PUPPET_BRACKETS", ["punctuation.section", "meta.brace", "punctuation"]),
    ("PUPPET_CLASS", ["entity.name.class", "entity.name.type", "support.class"]),
    ("PUPPET_COMMA", ["punctuation.separator", "punctuation"]),
    ("PUPPET_DOT", ["punctuation.accessor", "punctuation"]),
    ("PUPPET_ESCAPE_SEQUENCE", ["constant.character.escape", "constant.character"]),
    ("PUPPET_KEYWORD", ["keyword", "storage.type"]),
    ("PUPPET_NUMBER", ["constant.numeric", "constant.language"]),
    ("PUPPET_OPERATION_SIGN", ["keyword.operator"]),
    ("PUPPET_PARENTH", ["meta.brace", "punctuation"]),
    ("PUPPET_REGEX", ["string.regexp", "string"]),
    ("PUPPET_RESOURCE_REFERENCE", ["entity.name.type", "support.type", "support.class"]),
    ("PUPPET_SEMICOLON", ["punctuation.terminator", "punctuation.separator", "punctuation"]),
    ("PUPPET_SQ_STRING", ["string"]),
    ("PUPPET_STRING", ["string"]),
    ("PUPPET_VARIABLE", ["variable", "variable.other"]),
    ("PUPPET_VARIABLE_INTERPOLATION", ["variable", "variable.other"]),

    # Slim / Haml templates
    ("SLIM_BAD_CHARACTER", ["invalid", "invalid.illegal"]),
    ("SLIM_CALL", ["entity.name.function", "support.function", "variable.function"]),
    ("SLIM_CLASS", ["entity.other.attribute-name.class", "entity.name.label", "keyword"]),
    ("SLIM_COMMENT", ["comment", "comment.line", "comment.block"]),
    ("SLIM_DOCTYPE_KWD", ["keyword", "storage.type"]),
    ("SLIM_FILTER", ["keyword", "storage.type"]),
    ("SLIM_FILTER_CONTENT", ["string"]),
    ("SLIM_ID", ["entity.other.attribute-name.id", "entity.name.label", "keyword"]),
    ("SLIM_INTERPOLATION", ["variable", "variable.other"]),
    ("SLIM_PARENTHS", ["meta.brace", "punctuation"]),
    ("SLIM_RUBY_CODE", ["variable", "identifier"]),
    ("SLIM_STATIC_CONTENT", ["variable", "identifier"]),
    ("SLIM_STRING_INTERPOLATED", ["string"]),
    ("SLIM_TAG", ["entity.name.tag", "meta.tag", "tag"]),
    ("SLIM_TAG_ATTR_KEY", ["entity.other.attribute-name", "meta.attribute", "attribute"]),
    ("SLIM_TAG_START", ["entity.name.tag", "meta.tag", "tag"]),
    ("HAML_CLASS", ["entity.other.attribute-name.class", "entity.name.label", "keyword"]),
    ("HAML_COMMENT", ["comment", "comment.line", "comment.block"]),
    ("HAML_FILTER", ["keyword", "storage.type"]),
    ("HAML_FILTER_CONTENT", ["string"]),
    ("HAML_ID", ["entity.other.attribute-name.id", "entity.name.label", "keyword"]),
    ("HAML_LINE_CONTINUATION", ["punctuation", "keyword.operator"]),
    ("HAML_PARENTHS", ["meta.brace", "punctuation"]),
    ("HAML_RUBY_CODE", ["variable", "identifier"]),
    ("HAML_RUBY_START", ["punctuation", "keyword.operator"]),
    ("HAML_STRING", ["string"]),
    ("HAML_STRING_INTERPOLATED", ["string"]),
    ("HAML_TAG", ["entity.name.tag", "meta.tag", "tag"]),
    ("HAML_TAG_NAME", ["entity.name.tag", "meta.tag", "tag"]),
    ("HAML_TEXT", ["variable", "identifier"]),
    ("HAML_WS_REMOVAL", ["punctuation", "keyword.operator"]),
    ("HAML_XHTML", ["entity.name.tag", "meta.tag", "tag"]),
]


COLOR_SOURCES = [
    ("CONSOLE_BACKGROUND_KEY", ["terminal.background", "editor.background"]),
    ("GUTTER_BACKGROUND", ["editorGroup.background", "editor.background"]),
    ("EDITOR_GUTTER_BACKGROUND", ["editorGroup.background", "editor.background"]),
    ("CARET_COLOR", ["editorCursor.foreground", "terminalCursor.foreground"]),
    ("CARET_ROW_COLOR", ["editor.lineHighlightBackground"]),
    ("LINE_NUMBERS_COLOR", ["editorLineNumber.foreground"]),
    ("LINE_NUMBER_ON_CARET_ROW_COLOR", ["editorLineNumber.activeForeground"]),
    ("SELECTION_BACKGROUND", ["editor.selectionBackground", "editor.inactiveSelectionBackground"]),
    ("SELECTION_BACKGROUND_INACTIVE", ["editor.inactiveSelectionBackground"]),
    ("SELECTION_FOREGROUND", ["editor.foreground"]),
    ("WHITESPACES", ["editorWhitespace.foreground"]),
    ("INDENT_GUIDE", ["editorIndentGuide.background"]),
    ("SELECTED_INDENT_GUIDE", ["editorIndentGuide.activeBackground"]),
    ("MATCHED_BRACES_INDENT_GUIDE_COLOR", ["editorIndentGuide.activeBackground", "editorIndentGuide.background"]),
    ("VISUAL_INDENT_GUIDE", ["editorIndentGuide.activeBackground"]),
    ("STRING_CONTENT_INDENT_GUIDE", ["editorIndentGuide.background"]),
    ("SOFT_WRAP_SIGN_COLOR", ["editorWhitespace.foreground"]),
    ("TABS", ["editorWhitespace.foreground"]),
    ("RIGHT_MARGIN_COLOR", ["editorIndentGuide.activeBackground", "editorIndentGuide.background"]),
    ("ANNOTATIONS_COLOR", ["codeLens.foreground", "descriptionForeground"]),
    ("ANNOTATIONS_LAST_COMMIT_COLOR", ["gitDecoration.modifiedResourceForeground", "gitDecoration.changedResourceForeground"]),
    ("READONLY_BACKGROUND", ["editor.inactiveSelectionBackground", "editor.lineHighlightBackground"]),
    ("READONLY_FRAGMENT_BACKGROUND", ["editor.lineHighlightBackground"]),
    ("ADDED_LINES_COLOR", ["diffEditor.insertedTextBackground", "gitDecoration.addedResourceForeground"]),
    ("MODIFIED_LINES_COLOR", ["merge.commonContentBackground", "editor.lineHighlightBackground"]),
    ("DELETED_LINES_COLOR", ["diffEditor.removedTextBackground", "gitDecoration.deletedResourceForeground"]),
    ("WHITESPACES_MODIFIED_LINES_COLOR", ["merge.commonContentBackground"]),
    ("BORDER_LINES_COLOR", ["editorGroup.border", "sideBar.border", "editorIndentGuide.background"]),
    ("IGNORED_ADDED_LINES_BORDER_COLOR", ["gitDecoration.ignoredResourceForeground", "editorIndentGuide.background"]),
    ("IGNORED_MODIFIED_LINES_BORDER_COLOR", ["gitDecoration.ignoredResourceForeground", "editorIndentGuide.background"]),
    ("IGNORED_DELETED_LINES_BORDER_COLOR", ["gitDecoration.ignoredResourceForeground", "editorIndentGuide.background"]),
    ("CHANGED_LINES_POPUP", ["quickInput.background", "editorSuggestWidget.background"]),
    ("DIFF_SEPARATORS_BACKGROUND", ["panel.background", "sideBar.background"]),
    ("DIFF_SEPARATORS_TOP_BORDER", ["panel.border", "sideBar.border"]),
    ("DIFF_BLOCK_AREA_HIGHLIGHT_MARKER", ["gitDecoration.deletedResourceForeground", "editorOverviewRuler.deletedContent"]),
    ("NOTIFICATION_BACKGROUND", ["notifications.background", "quickInput.background"]),
    ("DOCUMENTATION_COLOR", ["quickInput.background", "panel.background"]),
    ("PREVIEW_BACKGROUND", ["editor.background", "editorGroup.background"]),
    ("PREVIEW_BORDER_COLOR", ["editorGroup.border", "sideBar.border"]),
    ("STICKY_LINES_BACKGROUND", ["editorGroupHeader.tabsBackground", "panel.background"]),
    ("STICKY_LINES_HOVERED_COLOR", ["editor.lineHighlightBackground"]),
    ("STICKY_LINES_BORDER_COLOR", ["editorGroup.border", "sideBar.border"]),
    ("FOLDED_TEXT_BORDER_COLOR", ["editorIndentGuide.background"]),
    ("BREADCRUMBS_BORDER_COLOR", ["editorIndentGuide.background", "panel.border"]),
    ("TAB_UNDERLINE", ["tab.activeBorder", "inputOption.activeBorder"]),
    ("TAB_UNDERLINE_INACTIVE", ["tab.border", "panel.border"]),
    ("MODIFIED_TAB_ICON", ["settings.modifiedItemIndicator", "gitDecoration.modifiedResourceForeground"]),

    # File status colors
    ("FILESTATUS_ADDED", ["gitDecoration.addedResourceForeground", "gitDecoration.untrackedResourceForeground"]),
    ("FILESTATUS_COPIED", ["gitDecoration.addedResourceForeground"]),
    ("FILESTATUS_DELETED", ["gitDecoration.deletedResourceForeground"]),
    ("FILESTATUS_HIJACKED", ["gitDecoration.conflictedResourceForeground", "warningForeground"]),
    ("FILESTATUS_IDEA_FILESTATUS_DELETED_FROM_FILE_SYSTEM", ["gitDecoration.deletedResourceForeground"]),
    ("FILESTATUS_IDEA_FILESTATUS_IGNORED", ["gitDecoration.ignoredResourceForeground"]),
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_BOTH_CONFLICTS", ["gitDecoration.conflictedResourceForeground"]),
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_CONFLICTS", ["gitDecoration.conflictedResourceForeground"]),
    ("FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_PROPERTY_CONFLICTS", ["gitDecoration.conflictedResourceForeground"]),
    ("FILESTATUS_IDEA_SVN_FILESTATUS_EXTERNAL", ["gitDecoration.addedResourceForeground"]),
    ("FILESTATUS_IDEA_SVN_FILESTATUS_OBSTRUCTED", ["gitDecoration.modifiedResourceForeground"]),
    ("FILESTATUS_IDEA_SVN_REPLACED", ["gitDecoration.modifiedResourceForeground"]),
    ("FILESTATUS_MERGED", ["gitDecoration.conflictedResourceForeground", "gitDecoration.modifiedResourceForeground"]),
    ("FILESTATUS_MODIFIED", ["gitDecoration.modifiedResourceForeground"]),
    ("FILESTATUS_NOT_CHANGED_IMMEDIATE", ["gitDecoration.modifiedResourceForeground"]),
    ("FILESTATUS_NOT_CHANGED_RECURSIVE", ["gitDecoration.modifiedResourceForeground"]),
    ("FILESTATUS_OBSOLETE", ["warningForeground", "gitDecoration.conflictedResourceForeground"]),
    ("FILESTATUS_SUPPRESSED", ["gitDecoration.ignoredResourceForeground"]),
    ("FILESTATUS_SWITCHED", ["gitDecoration.modifiedResourceForeground"]),
    ("FILESTATUS_UNKNOWN", ["errorForeground"]),
    ("FILESTATUS_addedOutside", ["gitDecoration.addedResourceForeground"]),
    ("FILESTATUS_changelistConflict", ["gitDecoration.conflictedResourceForeground"]),
    ("FILESTATUS_modifiedOutside", ["gitDecoration.modifiedResourceForeground"]),
]


def build_colors(colors, editor_background):
    entries = []
    for name, keys in COLOR_SOURCES:
        value = first_color(colors, *keys)
        hex_value = color_hex(value, editor_background)
        if hex_value:
            entries.append(f'    <option name="{name}" value="{hex_value}" />\n')
    return "  <colors>\n" + "".join(entries) + "  </colors>\n"


def explicit_attributes(colors, editor_background, rules):
    def color(key):
        return color_hex(colors.get(key))

    def blended(key):
        return color_hex(colors.get(key), editor_background)

    attrs = []

    def add(name, foreground=None, background=None, font_type=0,
            effect_type=None, effect_color=None, error_stripe=None):
        result = attribute_xml(name, foreground, background, font_type,
                               effect_type, effect_color, error_stripe)
        if result:
            attrs.append(result)

    def scoped(query):
        settings = resolve_scope(rules, query)
        return (color_hex(settings.get("foreground")),
                font_bits(settings.get("fontStyle", "")))

    add("BAD_CHARACTER", foreground=color("errorForeground"),
        background=color("editor.background"), error_stripe=color("errorForeground"))
    add("BREAKPOINT_ATTRIBUTES", foreground=color("errorForeground"))
    add("ERRORS_ATTRIBUTES", foreground=color("errorForeground"))
    add("WARNING_ATTRIBUTES", foreground=color("warningForeground"))
    add("INFO_ATTRIBUTES", foreground=color("infoForeground"))
    add("GENERIC_SERVER_ERROR_OR_WARNING", foreground=color("warningForeground"))
    add("TODO_DEFAULT_ATTRIBUTES", foreground=color("warningForeground"), font_type=1)
    deprecated_fg, deprecated_ft = scoped("invalid.deprecated")
    add("DEPRECATED_ATTRIBUTES", foreground=deprecated_fg, font_type=deprecated_ft)
    add("UNMATCHED_BRACE_ATTRIBUTES", foreground=color("errorForeground"))
    add("MATCHED_BRACE_ATTRIBUTES", foreground=color("inputOption.activeBorder"))
    comment_fg, comment_ft = scoped("comment")
    add("NOT_USED_ELEMENT_ATTRIBUTES", foreground=comment_fg, font_type=comment_ft)
    add("CONDITIONALLY_NOT_COMPILED", foreground=comment_fg, font_type=comment_ft)
    add("DUPLICATE_FROM_SERVER", foreground=color("gitDecoration.modifiedResourceForeground"))

    link = color("textLink.foreground")
    link_active = color("textLink.activeForeground")
    add("HYPERLINK_ATTRIBUTES", foreground=link, effect_type=1, effect_color=link)
    add("FOLLOWED_HYPERLINK_ATTRIBUTES", foreground=link_active, effect_type=1, effect_color=link_active)

    selection_bg = blended("editor.selectionBackground")
    foreground = color("editor.foreground")
    add("SEARCH_RESULT_ATTRIBUTES", foreground=foreground, background=selection_bg)
    add("TEXT_SEARCH_RESULT_ATTRIBUTES", foreground=foreground, background=selection_bg)
    add("WRITE_SEARCH_RESULT_ATTRIBUTES", foreground=foreground, background=selection_bg)
    add("LIVE_TEMPLATE_ATTRIBUTES", foreground=color("editorCursor.foreground"))
    add("LIVE_TEMPLATE_INACTIVE_SEGMENT", foreground=color("descriptionForeground"))
    add("FOLDED_TEXT_ATTRIBUTES", foreground=color("descriptionForeground"), font_type=2)
    add("DELETED_TEXT_ATTRIBUTES", foreground=color("gitDecoration.deletedResourceForeground"),
        background=blended("diffEditor.removedTextBackground"))
    add("INJECTED_LANGUAGE_FRAGMENT", foreground=foreground)
    add("CODE_LENS_BORDER_COLOR", foreground=color("codeLens.foreground"))

    add("BREADCRUMBS_DEFAULT", foreground=color("breadcrumb.foreground"))
    add("BREADCRUMBS_HOVERED", foreground=color("descriptionForeground"))
    add("BREADCRUMBS_CURRENT", foreground=color("breadcrumb.activeSelectionForeground"))
    add("BREADCRUMBS_INACTIVE", foreground=color("breadcrumb.foreground"))

    add("INLINE_SUGGESTION", foreground=color("descriptionForeground"))
    add("INLINE_PARAMETER_HINT", foreground=color("descriptionForeground"))
    add("INLINE_PARAMETER_HINT_HIGHLIGHTED", foreground=color("editorCursor.foreground"))
    add("INLINE_PARAMETER_HINT_CURRENT", foreground=color("textLink.foreground"))
    add("INLAY_DEFAULT", foreground=color("descriptionForeground"))
    add("INLAY_BUTTON_DEFAULT", foreground=color("descriptionForeground"),
        background=color("sideBarSectionHeader.background"))
    add("INLAY_BUTTON_FOCUSED", foreground=color("editor.foreground"),
        background=color("editor.lineHighlightBackground"))
    add("INLAY_BUTTON_HOVERED", foreground=color("editor.foreground"),
        background=color("editor.lineHighlightBackground"))
    add("AI_INLAY_BUTTON_DEFAULT", foreground=color("descriptionForeground"),
        background=color("sideBarSectionHeader.background"))
    add("AI_INLAY_BUTTON_FOCUSED", foreground=color("editor.foreground"),
        background=color("editor.lineHighlightBackground"))
    add("AI_INLAY_BUTTON_HOVERED", foreground=color("editor.foreground"),
        background=color("editor.lineHighlightBackground"))
    add("INLAY_BUTTON_HINT", foreground=color("descriptionForeground"))
    add("INLAY_TEXT_WITHOUT_BACKGROUND", foreground=color("descriptionForeground"))

    console = [
        ("CONSOLE_NORMAL_OUTPUT", "terminal.foreground"),
        ("CONSOLE_RED_OUTPUT", "terminal.ansiRed"),
        ("CONSOLE_GREEN_OUTPUT", "terminal.ansiGreen"),
        ("CONSOLE_YELLOW_OUTPUT", "terminal.ansiYellow"),
        ("CONSOLE_BLUE_OUTPUT", "terminal.ansiBlue"),
        ("CONSOLE_MAGENTA_OUTPUT", "terminal.ansiMagenta"),
        ("CONSOLE_CYAN_OUTPUT", "terminal.ansiCyan"),
        ("CONSOLE_GRAY_OUTPUT", "terminal.ansiBrightBlack"),
        ("CONSOLE_SYSTEM_OUTPUT", "descriptionForeground"),
        ("CONSOLE_USER_INPUT", "terminalCursor.foreground"),
        ("CONSOLE_ERROR_OUTPUT", "errorForeground"),
    ]
    for name, key in console:
        add(name, foreground=color(key))

    custom = [
        ("CUSTOM_KEYWORD1_ATTRIBUTES", "keyword"),
        ("CUSTOM_KEYWORD2_ATTRIBUTES", "keyword"),
        ("CUSTOM_KEYWORD3_ATTRIBUTES", "keyword"),
        ("CUSTOM_KEYWORD4_ATTRIBUTES", "keyword"),
        ("CUSTOM_STRING_ATTRIBUTES", "string"),
        ("CUSTOM_NUMBER_ATTRIBUTES", "constant.numeric"),
        ("CUSTOM_LINE_COMMENT_ATTRIBUTES", "comment"),
        ("CUSTOM_MULTI_LINE_COMMENT_ATTRIBUTES", "comment.block"),
        ("CUSTOM_VALID_STRING_ESCAPE_ATTRIBUTES", "constant.character.escape"),
        ("CUSTOM_INVALID_STRING_ESCAPE_ATTRIBUTES", "invalid"),
    ]
    for name, query in custom:
        foreground, font_type = scoped(query)
        add(name, foreground=foreground, font_type=font_type)

    buildout = [
        ("BUILDOUT.KEY", "entity.other.attribute-name"),
        ("BUILDOUT.KEY_VALUE_SEPARATOR", "keyword.operator"),
        ("BUILDOUT.LINE_COMMENT", "comment.line"),
        ("BUILDOUT.SECTION_NAME", "entity.name.section.ini"),
        ("BUILDOUT.VALUE", "string"),
    ]
    for name, query in buildout:
        foreground, font_type = scoped(query)
        add(name, foreground=foreground, font_type=font_type)

    return attrs


def build_scheme(vscode, parent_scheme):
    colors = vscode.get("colors", {})
    editor_background = parse_color(first_color(colors, "editor.background"))
    rules = token_rules(vscode)

    attributes = []
    text_foreground = color_hex(first_color(colors, "editor.foreground"))
    text_background = color_hex(first_color(colors, "editor.background"), editor_background)
    attributes.append(attribute_xml("TEXT", text_foreground, text_background))

    for name, queries in SCOPED_ATTRIBUTES:
        attributes.append(scoped_attribute(name, queries, rules, editor_background))

    attributes.extend(explicit_attributes(colors, editor_background, rules))
    attributes = [item for item in attributes if item]

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<scheme name="{escape(vscode["name"])}" version="{VERSION}" parent_scheme="{parent_scheme}">\n'
        + build_colors(colors, editor_background)
        + '  <attributes>\n'
        + "".join(attributes)
        + '  </attributes>\n'
        '</scheme>\n'
    )


def ui_hex(value):
    parsed = parse_color(value)
    if parsed is None:
        return None
    if parsed[3] == 255:
        return "#%02X%02X%02X" % parsed[:3]
    return "#%02X%02X%02X%02X" % parsed


def add_named_color(named, name, colors, *keys):
    value = first_color(colors, *keys)
    hex_value = ui_hex(value)
    if hex_value:
        named[name] = hex_value


def scheme_file_for_source(source):
    if "dark" in source:
        return "Orchids-Dark.xml"
    return "Orchids-Light.xml"


def build_ui_theme(vscode, spec):
    colors = vscode.get("colors", {})
    is_dark = vscode.get("type") == "dark"

    named = {}
    add_named_color(named, "editorBackground", colors, "editor.background")
    add_named_color(named, "editorForeground", colors, "editor.foreground")
    add_named_color(named, "chromeBackground", colors,
                    "sideBar.background", "activityBar.background", "titleBar.activeBackground")
    add_named_color(named, "chromeHeader", colors,
                    "editorGroupHeader.tabsBackground", "sideBar.background")
    add_named_color(named, "chromeRaised", colors,
                    "input.background", "dropdown.background", "quickInput.background",
                    "editorSuggestWidget.background")
    if is_dark:
        frame_keys = ["input.background", "sideBarSectionHeader.background",
                      "dropdown.background", "editor.lineHighlightBackground"]
    else:
        frame_keys = ["editorIndentGuide.background", "editorWhitespace.foreground",
                      "input.background", "sideBarSectionHeader.background"]
    add_named_color(named, "frameBackground", colors, *frame_keys)
    add_named_color(named, "popupBackground", colors,
                    "quickInput.background", "editorSuggestWidget.background",
                    "notifications.background", "input.background")
    add_named_color(named, "tooltipBackground", colors,
                    "quickInput.background", "panel.background", "input.background")
    add_named_color(named, "panelBackground", colors,
                    "panel.background", "sideBar.background", "activityBar.background")
    add_named_color(named, "toolbarBackground", colors,
                    "activityBar.background", "titleBar.activeBackground", "sideBar.background")
    add_named_color(named, "statusBarBackground", colors,
                    "statusBar.background", "activityBar.background", "sideBar.background")
    add_named_color(named, "tabBackground", colors,
                    "tab.inactiveBackground", "editorGroupHeader.tabsBackground", "sideBar.background")
    add_named_color(named, "activeTabBackground", colors,
                    "tab.activeBackground", "editor.background")
    add_named_color(named, "borderColor", colors,
                    "sideBar.border", "editorGroup.border", "panel.border", "tab.border")
    add_named_color(named, "separatorColor", colors,
                    "editorIndentGuide.background", "editorWhitespace.foreground", "tree.indentGuidesStroke")
    add_named_color(named, "hoverBackground", colors,
                    "list.hoverBackground", "settings.focusedRowBackground", "editor.lineHighlightBackground")
    add_named_color(named, "selectionBackground", colors,
                    "list.activeSelectionBackground", "list.focusBackground")
    add_named_color(named, "selectionInactiveBackground", colors,
                    "list.inactiveSelectionBackground", "editor.inactiveSelectionBackground")
    add_named_color(named, "selectionForeground", colors,
                    "list.activeSelectionForeground", "list.focusForeground", "editor.foreground")
    add_named_color(named, "disabledForeground", colors,
                    "input.placeholderForeground", "descriptionForeground", "breadcrumb.foreground")
    add_named_color(named, "focusColor", colors,
                    "inputOption.activeBorder", "settings.focusedItemBorder", "editorCursor.foreground")
    add_named_color(named, "accentColor", colors,
                    "button.background", "progressBar.background", "welcomePage.buttonBackground")
    add_named_color(named, "accentForeground", colors,
                    "button.foreground", "extensionButton.prominentForeground")
    add_named_color(named, "accentHover", colors,
                    "button.hoverBackground", "welcomePage.buttonHoverBackground")
    add_named_color(named, "linkColor", colors, "textLink.foreground")
    add_named_color(named, "linkActiveColor", colors, "textLink.activeForeground")
    add_named_color(named, "errorColor", colors, "errorForeground")
    add_named_color(named, "warningColor", colors, "warningForeground")
    add_named_color(named, "infoColor", colors, "infoForeground")
    add_named_color(named, "descriptionColor", colors,
                    "descriptionForeground", "codeLens.foreground", "breadcrumb.foreground")
    add_named_color(named, "modifiedItemColor", colors,
                    "settings.modifiedItemIndicator", "gitDecoration.modifiedResourceForeground")
    add_named_color(named, "addedColor", colors,
                    "gitDecoration.addedResourceForeground", "gitDecoration.untrackedResourceForeground")
    add_named_color(named, "deletedColor", colors,
                    "gitDecoration.deletedResourceForeground", "diffEditor.removedTextBorder")
    add_named_color(named, "conflictColor", colors,
                    "gitDecoration.conflictedResourceForeground", "warningForeground")
    add_named_color(named, "caretColor", colors,
                    "editorCursor.foreground", "terminalCursor.foreground")
    add_named_color(named, "lineHighlight", colors, "editor.lineHighlightBackground")

    ui = {
        "*": {
            "foreground": "editorForeground",
            "background": "chromeBackground",
            "inactiveBackground": "chromeBackground",
            "borderColor": "borderColor",
            "disabledText": "disabledForeground",
            "disabledForeground": "disabledForeground",
            "disabledBackground": "chromeRaised",
            "disabledBorderColor": "separatorColor",
            "selectionBackground": "selectionBackground",
            "lightSelectionBackground": "selectionBackground",
            "selectionInactiveBackground": "selectionInactiveBackground",
            "selectionForeground": "selectionForeground",
            "selectionInactiveForeground": "descriptionColor",
            "hoverBackground": "hoverBackground",
            "infoForeground": "infoColor",
            "acceleratorForeground": "disabledForeground",
            "shortcutForeground": "disabledForeground",
            "underlineColor": "focusColor",
            "inactiveUnderlineColor": "disabledForeground",
            "focusColor": "focusColor",
            "separatorColor": "separatorColor",
            "separatorForeground": "disabledForeground",
            "modifiedItemForeground": "modifiedItemColor",
        },
        "MainWindow": {
            "background": "frameBackground",
        },
        "MainToolbar": {
            "background": "chromeBackground",
            "borderColor": "separatorColor",
        },
        "StatusBar": {
            "background": "statusBarBackground",
            "borderColor": "borderColor",
        },
        "TitlePane": {
            "background": "chromeBackground",
            "foreground": "editorForeground",
        },
        "ToolWindow": {
            "background": "chromeBackground",
            "Header": {
                "background": "chromeRaised",
                "inactiveBackground": "chromeRaised",
                "borderColor": "separatorColor",
            },
            "Stripe": {
                "borderColor": "separatorColor",
            },
            "HeaderTab": {
                "underlinedTabBackground": "chromeRaised",
                "underlineColor": "focusColor",
            },
            "Button": {
                "selectedBackground": "selectionBackground",
            },
        },
        "Editor": {
            "background": "editorBackground",
            "Toolbar": {
                "borderColor": "separatorColor",
            },
            "SearchField": {
                "background": "chromeRaised",
            },
            "ToolTip": {
                "foreground": "editorForeground",
                "background": "tooltipBackground",
                "border": "borderColor",
                "selectionBackground": "selectionBackground",
                "selectionForeground": "selectionForeground",
            },
        },
        "EditorPane": {
            "splitBorder": "separatorColor",
        },
        "EditorTabs": {
            "background": "editorBackground",
            "hoverBackground": "hoverBackground",
            "hoverInactiveBackground": "hoverBackground",
            "underTabsBorderColor": "separatorColor",
            "underlineColor": "focusColor",
            "inactiveUnderlineColor": "disabledForeground",
            "underlinedTabBackground": "chromeRaised",
            "inactiveUnderlinedTabBackground": "editorBackground",
            "underlinedBorderColor": "focusColor",
            "inactiveUnderlinedTabBorderColor": "borderColor",
            "inactiveColoredFileBackground": "chromeRaised",
            "unselectedBlend": 0.85,
        },
        "DefaultTabs": {
            "background": "chromeBackground",
            "hoverBackground": "hoverBackground",
            "underlineColor": "focusColor",
            "inactiveUnderlineColor": "disabledForeground",
            "underlinedTabBackground": "chromeRaised",
            "inactiveUnderlinedTabBackground": "chromeBackground",
        },
        "Borders": {
            "color": "borderColor",
            "ContrastBorderColor": "separatorColor",
        },
        "Component": {
            "borderColor": "borderColor",
            "focusedBorderColor": "focusColor",
            "errorFocusColor": "errorColor",
            "inactiveErrorFocusColor": "errorColor",
            "warningFocusColor": "warningColor",
            "inactiveWarningFocusColor": "warningColor",
            "iconColor": "editorForeground",
        },
        "ActionButton": {
            "hoverBackground": "hoverBackground",
            "pressedBackground": "selectionInactiveBackground",
            "hoverBorderColor": "borderColor",
            "pressedBorderColor": "borderColor",
            "focusedBorderColor": "focusColor",
        },
        "Button": {
            "background": "chromeRaised",
            "foreground": "editorForeground",
            "startBackground": "chromeRaised",
            "endBackground": "chromeRaised",
            "startBorderColor": "borderColor",
            "endBorderColor": "borderColor",
            "focusedBorderColor": "focusColor",
            "disabledBorderColor": "separatorColor",
            "default": {
                "foreground": "accentForeground",
                "startBackground": "accentColor",
                "endBackground": "accentColor",
                "startBorderColor": "accentColor",
                "endBorderColor": "accentColor",
                "focusedBorderColor": "focusColor",
            },
        },
        "CheckBox": {
            "background": "chromeRaised",
        },
        "ComboBox": {
            "background": "chromeRaised",
            "nonEditableBackground": "chromeRaised",
            "disabledBackground": "chromeBackground",
            "selectionBackground": "selectionBackground",
            "ArrowButton": {
                "background": "chromeRaised",
                "nonEditableBackground": "chromeRaised",
            },
        },
        "TextField": {
            "background": "chromeRaised",
            "foreground": "editorForeground",
            "caretForeground": "caretColor",
            "selectionBackground": "selectionBackground",
            "selectionForeground": "selectionForeground",
            "inactiveForeground": "disabledForeground",
        },
        "Popup": {
            "background": "popupBackground",
            "borderColor": "borderColor",
        },
        "PopupMenu": {
            "background": "popupBackground",
            "borderColor": "borderColor",
            "selectionBackground": "selectionBackground",
            "selectionForeground": "selectionForeground",
        },
        "Menu": {
            "background": "popupBackground",
            "borderColor": "borderColor",
        },
        "MenuItem": {
            "background": "popupBackground",
            "selectionBackground": "selectionBackground",
        },
        "List": {
            "background": "chromeRaised",
            "hoverBackground": "hoverBackground",
            "selectionBackground": "selectionBackground",
            "selectionForeground": "selectionForeground",
            "inactiveSelectionBackground": "selectionInactiveBackground",
        },
        "Tree": {
            "background": "chromeBackground",
            "hoverBackground": "hoverBackground",
            "selectionBackground": "selectionBackground",
            "selectionForeground": "selectionForeground",
        },
        "Table": {
            "background": "chromeRaised",
            "hoverBackground": "hoverBackground",
            "selectionBackground": "selectionBackground",
            "selectionForeground": "selectionForeground",
        },
        "SearchEverywhere": {
            "background": "popupBackground",
        },
        "Notifications": {
            "background": "popupBackground",
            "borderColor": "borderColor",
            "foreground": "editorForeground",
        },
        "Balloon": {
            "background": "popupBackground",
            "borderColor": "borderColor",
        },
        "Link": {
            "foreground": "linkColor",
            "activeForeground": "linkActiveColor",
            "hoverForeground": "linkActiveColor",
            "pressedForeground": "linkActiveColor",
            "visitedForeground": "linkColor",
            "focusedBorderColor": "focusColor",
        },
        "Label": {
            "foreground": "editorForeground",
            "errorForeground": "errorColor",
            "warningForeground": "warningColor",
        },
        "ProgressBar": {
            "progressColor": "accentColor",
        },
        "ProgressIcon": {
            "color": "accentColor",
        },
        "Counter": {
            "background": "accentColor",
            "foreground": "accentForeground",
        },
        "ScrollBar": {
            "thumbColor": "separatorColor",
            "hoverThumbColor": "disabledForeground",
            "pressedThumbColor": "focusColor",
        },
    }

    if spec["variant"] == "islands":
        ui["Islands"] = 1
        ui["Island"] = {
            "borderColor": "chromeBackground",
        }

    theme = {
        "name": spec["name"],
        "dark": is_dark,
        "author": PLUGIN_VENDOR,
        "editorScheme": "/themes/" + scheme_file_for_source(spec["source"]),
        "parentTheme": spec["parent_theme"],
        "colors": named,
        "ui": ui,
    }
    return json.dumps(theme, indent=2, ensure_ascii=False) + "\n"


def build_plugin_xml():
    providers = []
    for spec in UI_THEME_SPECS:
        providers.append(
            f'    <themeProvider id="{PLUGIN_ID}.{spec["provider_key"]}" '
            f'path="/themes/{spec["file"]}" targetUi="{spec["target_ui"]}"/>'
        )
    schemes = [
        '    <bundledColorScheme id="Orchids Dark" path="/themes/Orchids-Dark"/>',
        '    <bundledColorScheme id="Orchids Light" path="/themes/Orchids-Light"/>',
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<idea-plugin>\n'
        f'  <id>{PLUGIN_ID}</id>\n'
        f'  <name>{PLUGIN_NAME}</name>\n'
        f'  <version>{PLUGIN_VERSION}</version>\n'
        f'  <vendor url="{PLUGIN_VENDOR_URL}">{PLUGIN_VENDOR}</vendor>\n'
        f'  <idea-version since-build="{PLUGIN_SINCE_BUILD}"/>\n'
        '  <depends>com.intellij.modules.platform</depends>\n'
        '  <description><![CDATA[\n'
        '    Orchids light and dark themes for IntelliJ-based IDEs, generated from\n'
        '    the VS Code theme sources. Includes editor color schemes plus New UI\n'
        '    and Islands UI theme variants.\n'
        '  ]]></description>\n'
        '  <extensions defaultExtensionNs="com.intellij">\n'
        + "\n".join(providers + schemes)
        + '\n  </extensions>\n'
        '</idea-plugin>\n'
    )


def write_plugin():
    os.makedirs(PLUGIN_META_DIR, exist_ok=True)
    os.makedirs(PLUGIN_THEMES_DIR, exist_ok=True)

    plugin_xml = build_plugin_xml()
    with open(os.path.join(PLUGIN_META_DIR, "plugin.xml"), "w", encoding="utf-8") as handle:
        handle.write(plugin_xml)

    for source, _, icls_name in THEMES:
        with open(os.path.join(INTELLIJ_THEMES_DIR, icls_name), encoding="utf-8") as handle:
            scheme = handle.read()
        xml_name = icls_name[:-5] + ".xml" if icls_name.endswith(".icls") else icls_name + ".xml"
        with open(os.path.join(PLUGIN_THEMES_DIR, xml_name), "w", encoding="utf-8") as handle:
            handle.write(scheme)

    for spec in UI_THEME_SPECS:
        with open(os.path.join(INTELLIJ_THEMES_DIR, spec["file"]), encoding="utf-8") as handle:
            theme_json = handle.read()
        with open(os.path.join(PLUGIN_THEMES_DIR, spec["file"]), "w", encoding="utf-8") as handle:
            handle.write(theme_json)


def write_plugin_zip():
    os.makedirs(DIST_DIR, exist_ok=True)
    with zipfile.ZipFile(PLUGIN_ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        for dirpath, _, filenames in os.walk(PLUGIN_DIR):
            for filename in sorted(filenames):
                path = os.path.join(dirpath, filename)
                arcname = os.path.relpath(path, PLUGIN_DIR).replace(os.sep, "/")
                info = zipfile.ZipInfo(arcname, date_time=(2024, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                with open(path, "rb") as handle:
                    archive.writestr(info, handle.read())


def main():
    os.makedirs(INTELLIJ_THEMES_DIR, exist_ok=True)

    vscode_cache = {}

    def load_vscode(source):
        if source not in vscode_cache:
            with open(os.path.join(VSCODE_THEMES, source), encoding="utf-8") as handle:
                vscode_cache[source] = json.load(handle)
        return vscode_cache[source]

    for source, parent, output in THEMES:
        vscode = load_vscode(source)
        scheme = build_scheme(vscode, parent)
        path = os.path.join(INTELLIJ_THEMES_DIR, output)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(scheme)
        print(f"Wrote {path}")

    for spec in UI_THEME_SPECS:
        vscode = load_vscode(spec["source"])
        theme_json = build_ui_theme(vscode, spec)
        path = os.path.join(INTELLIJ_THEMES_DIR, spec["file"])
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(theme_json)
        print(f"Wrote {path}")

    write_plugin()
    print(f"Wrote {PLUGIN_DIR}")
    write_plugin_zip()
    print(f"Wrote {PLUGIN_ZIP}")


if __name__ == "__main__":
    main()
