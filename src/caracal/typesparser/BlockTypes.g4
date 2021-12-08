grammar BlockTypes;

block_types
   : block_type_definition+ EOF
   ;


block_type_definition:
    attributes
    NODE ident COLON
    ( properties_section
    | handlers_section
    | events_section
    | predicates_section)+
    ;

attributes: attribute*;
attribute: AT ident (LPAREN (attr_param (COMMA attr_param)*)? RPAREN);
attr_param: ident ASSIGN attr_param_value;
attr_param_value: string | integer;

string: STRING_LITERAL;
integer: INTEGER;


properties_section: PROPERTIES COLON properties;
properties: prop*;

handlers_section: HANDLERS COLON handlers;
handlers: handler*;

events_section: EVENTS COLON events;
events: event*;

predicates_section: PREDICATES COLON predicates;
predicates: pred*;

prop: prop_name COLON block_type prop_initialization?
    ;

prop_initialization: LPAREN (FLOAT | INTEGER | STRING_LITERAL) RPAREN;

prop_name: ident QUESTION_MARK?
    ;

event: ident LPAREN func_arguments RPAREN
    ;

handler: handler_name LPAREN func_arguments RPAREN
    ;

func_arguments: argument (COMMA argument)*
    ;

argument: ident COLON block_type
    ;

handler_name: ident PLUS?
    ;

block_type: IDENT (LPAREN block_type (COMMA block_type)* RPAREN)?
    ;

ident: IDENT;

pred: logical_expr;

logical_expr: expr (EQ | NEQ) expr
    | logical_expr (OR | AND) logical_expr
    ;

expr: ident
    | INTEGER
    | LPAREN expr RPAREN
    | ident LPAREN expr RPAREN
    | expr LBRACKET expr RBRACKET
    | expr DOT ident
    ;


WS
   : [ \t\r\n] -> skip
   ;


COLON
   : ':'
   ;

DOT : '.' ;


QUESTION_MARK: '?';
PLUS: '+' ;

LPAREN: '(' ;

RPAREN: ')' ;

AT: '@';

OR: 'or';
AND: 'and';

ASSIGN: '=';
EQ: '==';

NEQ: '!=';

LBRACKET: '[';
RBRACKET: ']';

COMMA: ',' ;

NODE: 'node';

PROPERTIES
       : 'properties'
   ;

EVENTS
   : 'events'
   ;

HANDLERS
   : 'handlers'
   ;

PREDICATES
   : 'predicates'
   ;

STRING_LITERAL : '"' (~('"' | '\\' | '\r' | '\n') | '\\' ('"' | '\\'))* '"';

INTEGER
   :  '0'
   | '1' .. '9' ('0' .. '9')*
   ;

FLOAT
   : ('0' .. '9') + ('.' ('0' .. '9') + )?
   ;

IDENT
   : ('a' .. 'z' | 'A' .. 'Z') ('a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '_')*
   ;



BLOCKCOMMENT
    :   '/*' .*? '*/' -> skip
    ;

LINECOMMENT
    :   '//' ~[\r\n]* -> skip
    ;
