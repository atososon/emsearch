import os
from emparser.preprocess import Lexer
import re
import pickle
from pathlib import Path
import glob
from collections import defaultdict

DATA_DIR = Path("emparser/data")
ABS_DIR = os.path.join(DATA_DIR, 'mml.vct')
lexer = Lexer()
lexer.load_symbol_dict(ABS_DIR)
lexer.build_len2symbol()
RESERVED_WORDS = ["according", "aggregate", "all", "and", "antonym", "are", "as", "associativity", "assume", "asymmetry", "attr",
                  "be", "begin", "being", "by", "canceled", "case", "cases", "cluster", "coherence", "commutativity", "compatibility", 
                  "connectedness", "consider", "consistency", "constructors", "contradiction", "correctness", "def", "deffunc", "define",
                  "definition", "definitions", "defpred", "do", "does", "end", "environ", "equals", "ex", "exactly", "existence", "for",
                  "from", "func", "given", "hence", "hereby", "holds", "idempotence", "identify", "if", "iff", "implies", "involutiveness",
                  "irreflexivity", "is", "it", "let", "means", "mode", "non", "not", "notation", "notations", "now", "of", "or", "otherwise",
                  "over", "per", "pred", "prefix", "projectivity", "proof", "provided", "qua", "reconsider", "reduce", "reducibility",
                  "redefine", "reflexivity", "registration", "registrations", "requirements", "reserve", "sch", "scheme", "schemes",
                  "section", "selector", "set", "sethood", "st", "struct", "such", "suppose", "symmetry", "synonym", "take", "that", "the", 
                  "then", "theorem", "theorems", "thesis", "thus", "to", "transitivity", "uniqueness", "vocabularies", "when", "where",
                  "with", "wrt", ",", ";", ":", "(", ")", "[", "]", "{", "}", "=", "&", "->", ".=", "...", "$1", "$2", "$3", "$4", "$5",
                  "$6", "&7", "$8", "$9", "$10", "(#", "#)"]

def is_variable(word):
    # 変数ならTrueを返し、そうでないならFalseを返す関数
    if word in RESERVED_WORDS or word.isdecimal() or "__" in word and "_" in word.replace("__", ""):
        return False
    else:
        return True


def create_abs_dictionary():
    # (definition or theorem)  (行数)  (ファイル名)  (ラベル名)       (テキスト)
    # definition               51      abcmiz_0.abs  BCMIZ_0:def 1   let T be RelStr;   attr T is Noetherian means   the InternalRel of T is co-well_founded; 

    cwd = os.getcwd()
    try:
        path = "./abstr"
        os.chdir(path)
        abs_files = sorted(glob.glob("*.abs"))
    finally:
        os.chdir(cwd)

    with open ("abs_dictionary.txt", "w") as abs_dictionary_file:
        for file in abs_files:
            with open(os.path.join("./abstr/", file), "r") as f:
                lines = f.readlines()

                is_definition_block = False # definitionのブロック内にあるかどうか  definition ~~ end; までの部分

                is_theorem = False # theoremの中にあるかどうか　theorem ~~ ; までの部分

                is_definition = False # definitionのラベル内かどうか
                
                common_definition_statement = [] # 変数定義などのdefinitionの共通部分の要素

                indivisual_definition_statement = [] # definitionのラベルごとの要素

                # abs_dictionaryに保存する情報
                item = {
                    "title": "",
                    "line_no": "",
                    "filename": file,
                    "label": "",
                    "text": ""
                }

                for line_no, line in enumerate(lines):

                    line = line.strip() # 改行文字を除くため
                    words = line.split()

                    for word_no, word in enumerate(words): 
                        if word == "::" and word_no == False and is_definition_block == False and is_theorem == False:
                            break

                        elif word == "theorem" and word_no == 0:
                            is_theorem = True
                            item["title"] = "theorem"
                            item["line_no"] = line_no
                            item["label"] = line.split('::')[1]
                            if bool(re.search(r"\w+:\w+", line.split('::')[1])):
                                item["label"] = line.split('::')[1]
                            break

                        elif is_theorem:
                            # コメントの場合は無視
                            if word == "::":
                                break
                            item["text"] += " " + word

                            # ";"はtheoremの最後の文字なため、改行しtheoremに関する変数を初期化している
                            if word[-1] == ";":
                                if item["label"] != "":
                                    abs_dictionary_file.write(f"{item['title']} {item['line_no']} {item['filename']} {item['label']} {item['text']}\n")
                                item = {
                                    "title": "",
                                    "line_no": "",
                                    "filename": file,
                                    "label": "",
                                    "text": ""
                                }
                                is_theorem = False
                                theorem_line_no = False
                                is_comment = False

                        elif word == "definition" and word_no == 0:
                            is_definition_block = True
                            item["title"] = "definition"

                        elif is_definition_block == True:
                            
                            if "end" in line and ";" in line:
                                is_definition_block = False
                                is_definition = False
                                common_definition_statement = []
                                indivisual_definition_statement = []
                                break
                            
                            elif word == ":::":
                                break
                            
                            elif not is_definition and word != "::":
                                # definition let ~
                                # 等の場合があるためdefinitionが含まれていたら除く
                                common_definition_statement.append(line.replace("definition", ""))
                                break
                            
                            # definition内かつ最終行でない場合のとき
                            elif is_definition and ";" not in line:
                                indivisual_definition_statement.append(line)
                                break
                            
                            # definitionのラベルがある場合
                            elif word == "::" and not is_definition:
                                is_definition = True
                                # line.split('::')[1].replace(' ','')はラベル名、のちの処理を簡略するためラベル名にある" "を除いている
                                # 例
                                # ABCMIZ_0:def 1 -> ABCMIZ_0:def1
                                item["title"] = "definition"
                                item["line_no"] = line_no
                                if bool(re.search(r"\w+:\w+", line.split('::')[1].replace(' ',''))):
                                    item["label"] = line.split('::')[1].replace(' ','')
                                if common_definition_statement:
                                    while common_definition_statement[-1][-1] != ";":
                                        indivisual_definition_statement.append(common_definition_statement.pop())
                                        if not common_definition_statement:
                                            break
                                break

                            # definitionのラベル部分の最後
                            elif ";" in line and is_definition:
                                indivisual_definition_statement.append(line)
                                is_definition = False
                                item["text"] = ' '.join(common_definition_statement) + " " + ' '.join(indivisual_definition_statement)
                                if item["label"]:
                                    abs_dictionary_file.write(f"{item['title']} {item['line_no']} {item['filename']} {item['label']} {item['text']}\n")
                                item = {
                                    "title": "",
                                    "line_no": "",
                                    "filename": file,
                                    "label": "",
                                    "text": ""
                                }
                                indivisual_definition_statement = []
                                break

def processing_variables_with_emparser(line, lexer):
    """
    変数を___に変更し、最期に変数の種類と数を入れている
    例
    line
    let T be RelStr;   attr T is Noetherian means   the InternalRel of T is co-well_founded; 
    return
    let ___ be RelStr ; attr ___ is Noetherian means the InternalRel of ___ is co-well_founded ; 1 3 
    """

    variable2appearance = defaultdict(int)

    lines = ("begin\n " + " ".join(line)).split(" ")
    env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
    env_lines = lexer.remove_comment(env_lines)
    text_proper_lines = lexer.remove_comment(text_proper_lines)
    tokenized_lines, position_map = lexer.lex(text_proper_lines)

    for i in range(1, len(tokenized_lines)): # tokenized_linesの先頭はbeginのため
        if is_variable(tokenized_lines[i]): # 変数の場合
            variable2appearance[tokenized_lines[i]] += 1
            tokenized_lines[i] = "___"
        tokenized_lines[i] = re.sub("__[^_]+_", "", tokenized_lines[i])

    return f"{' '.join(tokenized_lines[1:])} {'____ '*len(variable2appearance)}"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              

def create_document_vectors():
    """
    abs_dictionary.txt からdocument_vectors.txtを作成する関数
    変数を___に変更し、最期に変数の種類と数を入れている
    例
    abs_dictionary.txt
    definition 51 abcmiz_0.abs BCMIZ_0:def 1   let T be RelStr;   attr T is Noetherian means   the InternalRel of T is co-well_founded; 
        
    document_vectors.txt
    let ___ be RelStr ; attr ___ is Noetherian means the InternalRel of ___ is co-well_founded ; 1 3 
    """

    with open("document_vectors.txt", "w") as file_document_vectors:
        with open("abs_dictionary.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.replace(",", " ")
                line = line.replace(";", "")
                line = line.split()
                file_document_vectors.write(f"{processing_variables_with_emparser(line[4:])} \n")

def save_abs_dictionary_by_byte():
    """
    abs_dictionary.txtを行ごとにバイト数を求め、tell.pklに保存する関数
    """
    with open("abs_dictionary.txt", "rb") as f:
        tell = []
        tell_append = tell.append
        tell_append(0)
        with open("tell.pkl", "wb") as fi:
            while True:
                a = f.readline()
                if not a:
                    break
                tell_append(f.tell())

            pickle.dump(tell, fi)
