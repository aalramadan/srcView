import requests
import os
import subprocess

import pylibsrcml
import srcml_database

TAGS = ["actor","alias","alignas","alignof","annotation","annotation_defn","argument","argument_list","array","asm","assert",
        "associatedtype","association","association_list","atomic","attribute","block","block[@type=\"pseudo\"]","block_content",
        "box","break","by","calibration","call","capture","case","cast","catch","checked","class","class_decl","comment",
        "comment[@type=\"block\"]","comment[@type=\"docstring\"]","comment[@type=\"hashbang\"]","comment[@type=\"html\"]",
        "comment[@type=\"line\"]","comprehension","condition","constraint","constructor","constructor_decl","continue","control",
        "debugger","decl","decl[@type=\"const\"]","decl[@type=\"let\"]","decl[@type=\"static\"]","decl[@type=\"var\"]",
        "decl_stmt","decltype","default","defcalgrammar","defer","delay","delegate","destructor","destructor_decl","dictionary",
        "do","else","empty_stmt","end","enum","enum_decl","equals","escape","event","exec","export","expr","expr_stmt","extends",
        "extension","extern","fallthrough","finally","fixed","for","foreach","friend","from","function",
        "function[@type=\"generator\"]","function[@type=\"operator\"]","function_decl","gate","gate[@type=\"defcal\"]","gate_decl",
        "generic_selection","getter","global","goto","group","guard","if","if[@type=\"elseif\"]","if_stmt","implements","import",
        "in","include","incr","index","init","interface","interface_decl","into","join","label","lambda","lambda[@type=\"arrow\"]",
        "lambda[@type=\"generator\"]","let","linq","literal","literal[@type=\"boolean\"]","literal[@type=\"char\"]",
        "literal[@type=\"complex\"]","literal[@type=\"ellipsis\"]","literal[@type=\"null\"]","literal[@type=\"number\"]",
        "literal[@type=\"string\"]","literal[@type=\"qubit\"]","literal[@type=\"regex\"]","lock","macro","measure",
        "member_init_list","modifier","name","name_list","namespace","noexcept","nonlocal","object","on","operator","operator_decl",
        "orderby","package","parameter","parameter_list","pass","pragma","print","private","property","protected","protocol",
        "public","range","ref_qualifier","reset","return","select","selector","set","setter","sizeof","specifier","static",
        "struct","struct_decl","subscript","super","super_list","switch","synchronized","template","ternary","then","throw",
        "throws","try","tuple","type","type[@ref=\"previous\"]","typedef","typeid","typename","typeof","unchecked","union",
        "union_decl","unsafe","using","using_stmt","version","virtual","where","while","with","yield","yield[type=\"generator\"]",
        ]

"""
To download from GitHub:

Input Link: https://github.com/srcML/srcML
Download Link: https://github.com/srcML/srcML/archive/refs/heads/master.zip

"""

def download_github_repo(github_link):
    repo_name = "/".join(github_link.split("/")[-2:])
    download_link = github_link + "/archive/refs/heads/master.zip"
    save_location = "data/"+repo_name
    print(repo_name)
    if not os.path.isdir(save_location):
        os.makedirs(save_location)

    print("Downloading")
    #download the code
    response = requests.get(download_link,stream=True)
    if response.status_code == 200:
        with open(save_location+"/code.zip",'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    return False

def convert_to_srcml(repo_name,get_position=False):
    if not get_position:
        command = ["srcml","data/"+repo_name+"/code.zip","-o","data/"+repo_name+"/code.xml"]
    else:
        command = ["srcml","--position","data/"+repo_name+"/code.zip","-o","data/"+repo_name+"/code_pos.xml"]

    result = subprocess.run(command)

    if result.returncode == 0:
        return True
    else:
        return False

def add_srcml_to_database(repo_name):
    srcml_database.add_repo(repo_name)

    srcml = pylibsrcml.srcMLArchiveRead("data/"+repo_name+"/code_pos.xml")

    # Populate Files
    for unit in srcml:
        name = unit.get_filename()
        language = unit.get_language()
        srcml_database.add_file(name,language,repo_name)

    srcml_database.commit()
    return True

def run_stereocode(repo_name):
    command = ["./programs/stereocode", "data/"+repo_name+"/code_pos.xml","-o","data/"+repo_name+"/code_stereotype.xml"]

    result = subprocess.run(command)

    if result.returncode == 0:
        return True
    else:
        return False

def run_namecollector(repo_name):
    command = ["./programs/nameCollector","-i","data/"+repo_name+"/code_stereotype.xml","-o","data/"+repo_name+"/code_names.csv","--csv"]

    result = subprocess.run(command)

    if result.returncode == 0:
        return True
    else:
        return False

def add_names_to_database(repo_name):
    with open("data/"+repo_name+"/code_names.csv") as file:
        for line in file.readlines():
            line = line.strip()
            vals = line.split(",")
            name = vals[0]
            type = vals[1]
            category = vals[2]
            file = vals[3]
            pos = vals[4]
            stereotype = vals[6]
            srcml_database.add_identifier(name,type if type != "" else None,category,srcml_database.get_file_id_from_name_and_repo(file,srcml_database.get_repo_id_from_name(repo_name)),pos.split(":")[0],pos.split(":")[1],stereotype if stereotype != "" else None)
    srcml_database.commit()
    return True


def count_tags(repo_name):
    for tag in TAGS:
        with pylibsrcml.srcMLArchiveRead("data/"+repo_name+"/code.xml") as archive:
            archive.append_transform_xpath("count(//src:"+tag+")")
            for unit in archive:
                file = unit.get_filename()
                file_id = srcml_database.get_file_id_from_name_and_repo(file,srcml_database.get_repo_id_from_name(repo_name))
                result = archive.unit_apply_transforms(unit)
                srcml_database.add_tag_count(tag,file_id,result.get_number())

    srcml_database.commit()
    return True


