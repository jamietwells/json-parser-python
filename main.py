begin_array = '['
begin_object = '{'
end_array = ']'
end_object = '}'
name_separator = ':'
value_separator = ','
whitespace = [' ', '\t', '\n', '\r']

class JsonToken:
    def __init__(self, type):
        self.type = type
    def __repr__(self):
        def formatValue(value):
            if(isinstance(value, (JsonToken, list))):
                return repr(value)
            return value
        attributes = ', '.join(f"{k}='{formatValue(v)}'" for k, v in vars(self).items())
        return f"{self.__class__.__name__}({attributes})"
        
class JsonObject(JsonToken):
    def __init__(self, properties):
        super().__init__("Object")
        self.properties = properties
        
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

def parse_end_of_input(input_string):
    if not input_string:
        return True, input_string  # Fail if the string is empty
    return None, input_string  # No match found

def parse_test(predicate):
    def test(input_string):
        if not input_string:
            return None, input_string  # Fail if the string is empty
    
        first_char = input_string[0]
        if predicate(first_char):
            return first_char, input_string[1:]  # Return the matched char and remaining string
        else:
            return None, input_string  # No match found
    return test

parse_char = lambda char: parse_test(lambda inputChar: inputChar == char)
parse_any_of = lambda chars: parse_test(lambda inputChar: inputChar in chars)

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
parse_a = parse_char('a')
parse_e = parse_char('e')
parse_f = parse_char('f')
parse_l = parse_char('l')
parse_n = parse_char('n')
parse_r = parse_char('r')
parse_s = parse_char('s')
parse_t = parse_char('t')
parse_u = parse_char('u')

parse_quotation_mark = parse_char("\"")
parse_reverse_solidus = parse_char("\\")
parse_solidus = parse_char("/")
parse_backspace = parse_char("\b")
parse_form_feed = parse_char("\f")
parse_line_feed = parse_char("\n")
parse_carriage_return = parse_char("\r")
parse_tab = parse_char("\t")

# Combine them using the and_combinator
parse_true = and_combinator(parse_t, parse_r, parse_u, parse_e)(lambda _: JsonTrueLiteral())
parse_false = and_combinator(parse_f, parse_a, parse_l, parse_s, parse_e)(lambda _: JsonFalseLiteral())
parse_null = and_combinator(parse_n, parse_u, parse_l, parse_l)(lambda _: JsonNullLiteral())

escape_parsers = [parse_quotation_mark,parse_reverse_solidus,parse_solidus,parse_backspace,parse_form_feed,parse_line_feed,parse_carriage_return,parse_tab]

identity = lambda r: r

parse_escape_sequence = and_combinator(parse_reverse_solidus, or_combinator(*escape_parsers)(identity))(lambda r: r[1])

# Combine them using the or_combinator to parse the json literal
parse_literal = or_combinator(parse_true, parse_false, parse_null)(identity)

parse_whitespace = parse_any_of(whitespace)

parse_throw_whitespace = many_combinator(parse_whitespace)(lambda _: None)

def control_char(parser):
    return and_combinator(parse_throw_whitespace, parser, parse_throw_whitespace)(lambda r: r[1])
    
parse_begin_array = control_char(parse_char(begin_array))
parse_begin_object = control_char(parse_char(begin_object))
parse_end_array = control_char(parse_char(end_array))
parse_end_object = control_char(parse_char(end_object))
parse_name_separator = control_char(parse_char(name_separator))
parse_value_separator = control_char(parse_char(value_separator))

parse_digit = parse_any_of(['1','2','3','4','5','6','7','8','9','0'])

parse_dot = parse_char('.')

def array_to_string(arr):
    result = "";
    for i in arr:
      result += array_to_string(i) if isinstance(i, list) else i
    return result

parse_number = or_combinator(and_combinator(many_combinator(parse_digit)(identity), parse_dot, parse_digit, many_combinator(parse_digit)(identity))(identity), many_combinator(parse_digit)(identity))(lambda r: JsonNumber(array_to_string(r)))

parse_string = and_combinator(parse_quotation_mark, many_combinator(parse_test(lambda c: c != '"'))(identity), parse_quotation_mark)(lambda r: JsonString(array_to_string(r[1])))

parse_value = or_combinator(parse_literal, parse_string, parse_number)(identity)

parse_empty_array = and_combinator(parse_begin_array, parse_end_array)(lambda _: JsonArray([]))

parse_filled_array = and_combinator(parse_begin_array, parse_value, many_combinator(and_combinator(parse_value_separator, parse_value)(lambda r: r[1]))(identity), parse_end_array)(lambda v: JsonArray([v[1], *v[2]]))

parse_array = or_combinator(parse_empty_array, parse_filled_array)(identity)

parse_value = or_combinator(parse_array, parse_literal, parse_string, parse_number)(identity)

parse_json = and_combinator(parse_throw_whitespace, parse_value, parse_throw_whitespace, parse_end_of_input)(lambda r: r[1])

def printResult(output):
    result, remaining = output
    print(repr(result))
    
printResult(parse_json(" apple "))
printResult(parse_json(" true "))
printResult(parse_json("   false "))
printResult(parse_json(" null "))
printResult(parse_json(' "abc" '))
printResult(parse_json(' 123.456 '))
printResult(parse_json(' 123 '))
printResult(parse_json(' [ ] '))
printResult(parse_json(' [true,false , null , "abc",123.456,123  ] '))
