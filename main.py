begin_array = '['
begin_object = '{'
end_array = ']'
end_object = '}'
name_separator = ':'
value_separator = ';'
whitespace = [' ', '\t', '\n', '\r']

class JsonToken:
    def __init__(self, type):
        self.type = type
    def __repr__(self):
        attributes = ', '.join(f"{k}='{v}'" for k, v in vars(self).items())
        return f"{self.__class__.__name__}({attributes})"
        
class JsonObject(JsonToken):
    def __init__(self, value):
        super().__init__("Object")
        self.value = value
        
class JsonArray(JsonToken):
    def __init__(self, values):
        super().__init__("Array")
        self.values = values
        
class JsonNumber(JsonToken):
    def __init__(self, value):
        super().__init__("Number")
        self.value = value

class JsonString(JsonToken):
    def __init__(self, value):
        super().__init__("String")
        self.value = value

class JsonFalseLiteral(JsonToken):
    def __init__(self):
        super().__init__("False Literal")
        self.value = "false"

class JsonTrueLiteral(JsonToken):
    def __init__(self):
        super().__init__("True Literal")
        self.value = "true"

class JsonNullLiteral(JsonToken):
    def __init__(self):
        super().__init__("Null Literal")
        self.value = "null"
        
def parse_char(target_char, input_string):
    if not input_string:
        return None, input_string  # Fail if the string is empty

    first_char = input_string[0]
    if first_char == target_char:
        return first_char, input_string[1:]  # Return the matched char and remaining string
    else:
        return None, input_string  # No match found

def parse_any_of(chars, input_string):
    if not input_string:
        return None, input_string  # Fail if the string is empty

    first_char = input_string[0]
    if first_char in chars:
        return first_char, input_string[1:]  # Return the matched char and remaining string
    else:
        return None, input_string  # No match found

return_parser = lambda parser: lambda result_formatter: lambda input_string: parser(result_formatter, input_string)

def and_combinator(*parsers):
    def combined_parser(result_formatter, input_string):
        results = []
        current_input = input_string

        for parser in parsers:
            result, current_input = parser(current_input)
            if result is None:
                return None, input_string
            results.append(result)

        return result_formatter(results), current_input

    return return_parser(combined_parser)

def or_combinator(*parsers):
    def combined_parser(result_formatter, input_string):
        current_input = input_string

        for parser in parsers:
            result, current_input = parser(input_string)
            if result is not None:
                return result_formatter(result), current_input

        return None, input_string

    return return_parser(combined_parser)

def many_combinator(parser):
    def combined_parser(result_formatter, input_string):
        results = []
        current_input = input_string

        while True:
            result, current_input = parser(current_input)
            if result is None:
                return results, current_input
            results.append(result)

    return return_parser(combined_parser)

# Define the individual parsers
parse_a = lambda s: parse_char('a', s)
parse_e = lambda s: parse_char('e', s)
parse_f = lambda s: parse_char('f', s)
parse_l = lambda s: parse_char('l', s)
parse_n = lambda s: parse_char('n', s)
parse_r = lambda s: parse_char('r', s)
parse_s = lambda s: parse_char('s', s)
parse_t = lambda s: parse_char('t', s)
parse_u = lambda s: parse_char('u', s)

# Combine them using the and_combinator
parse_true = and_combinator(parse_t, parse_r, parse_u, parse_e)(lambda _: JsonTrueLiteral())
parse_false = and_combinator(parse_f, parse_a, parse_l, parse_s, parse_e)(lambda _: JsonFalseLiteral())
parse_null = and_combinator(parse_n, parse_u, parse_l, parse_l)(lambda _: JsonNullLiteral())


# Combine them using the or_combinator to parse the json literal
parse_literal = or_combinator(parse_true, parse_false, parse_null)(lambda r: r)

parse_whitespace = lambda s: parse_any_of(whitespace, s)

#parse_string = and_combinator(lambda s: parse_char('"', s), parse_string_internal, lambda s: parse_char('"', s))

parse_throw_whitespace = many_combinator(parse_whitespace)(lambda _: None)

parse_json = and_combinator(parse_throw_whitespace, parse_literal, parse_throw_whitespace)(lambda r: r[1])

def printResult(output):
    result, remaining = output
    print(repr(result))
    
printResult(parse_json(" apple "))
printResult(parse_json(" true "))
printResult(parse_json("   false "))
printResult(parse_json(" null "))
