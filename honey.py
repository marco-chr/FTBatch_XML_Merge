# libs
import os
import xml.etree.cElementTree as ET
import re

########################################################################################################################

# TODO recognize how many units
# TODO recognize unit letters and filter by unit
# TODO order properly operations
# TODO exe file

########################################################################################################################

print("I am making Honey for you!")

# up_list contains the names of unit operations scanned in the current dir
up_list = []

# general variables
debug = 1  # if 1 shows print messages

########################################################################################################################
########################################################################################################################

# open procedure
# Search uxml instances and related resource equipment

for file in os.listdir("."):
    if file.endswith(".pxml"):
        procedure_tree = ET.parse(file)
        procedure_root = procedure_tree.getroot()

        for child in procedure_root:
            if child.tag == '{urn:Rockwell/MasterRecipe}UnitRequirement':
                for el in child:
                    el.tag=re.sub('{[^>]+}', '', el.tag)
                    if el.tag == 'UnitAlias':
                        unit_alias = el.text.split(':')[0]
                    if el.tag == 'ClassInstance':
                        class_instance = el.text
                up_list.append([class_instance, unit_alias])

# print(up_list)

# for each uxml: open each uxml and record each step id name into array
for up in up_list:

    op_list = []
    unit_tree = ET.parse(up[1]+'.uxml')
    unit_root = unit_tree.getroot()

    for child in unit_root:
        if child.tag == '{urn:Rockwell/MasterRecipe}Steps':
            for el in child:
                if el.tag == '{urn:Rockwell/MasterRecipe}Step':
                    for sub_el in el:
                        if sub_el.tag == '{urn:Rockwell/MasterRecipe}StepRecipeID':
                            op_list.append(sub_el.text)

    # op list created

    #########################################################
    # Variable init                                         #
    #########################################################

    # instances contains last instance for each phase scanned
    instances = []
    # instances_substitutions contains original instance and new instance for the generated merged op
    instances_substitutions = []
    # transitions_substitutions contains original transition name and new transition name for the generated merged op
    transitions_substitutions = []
    # final null array
    null_instances = []

    max_y_current = 0
    max_y = 0
    op_delta = 0
    op_counter = 0

    transition_counter = 0
    transition_index = 0
    transition_global = 1

    link_counter = 0
    link_index = 0
    link_global = 1

    # scan dir to append filename to op_list array
    # regex find the op progressive number between _ chars and covert it to an integer
    # op list is made by a list of list with two elements (index, op name)

    # for file in os.listdir("."):
    #     if file.endswith(".oxml"):
    #         if file.find("_B_") != -1:
    #             if re.findall(r'_\d+_',file) != []:
    #                 op_index = int(re.findall(r'_\d+_',file)[0].strip('_'))
    #                 op_list.append([op_index,file])

    # sorting the list in order to concatenate operations in the intended order
    # op_list.sort()

    if debug == 1:
        print(op_list)

    # open first operation at index 0 and get root
    input_tree = ET.parse(op_list[0] + '.oxml')
    root = input_tree.getroot()

    # build filename for merged OP .oxml output
    # seqnumber_PA_regex="_" + str(op_list[0][0]) + "_[A-Z]+_"
    # seqnumber_PA = re.findall(seqnumber_PA_regex,op_list[0][1])[0]
    # op_filename = op_list[0][1].split(seqnumber_PA)[0] + "_" + op_list[0][1].split(seqnumber_PA)[1]

    op_filename = "OP_" + up[1].split("UP_")[1] + ".oxml"

    # build root element
    RecipeElement = ET.Element("RecipeElement")
    RecipeElement.attrib['SchemaVersion']="3528"
    RecipeElement.attrib['xmlns']="urn:Rockwell/MasterRecipe"
    RecipeElement.attrib['xmlns:xsd']="http://www.w3.org/2001/XMLSchema"

    # build 1st root child
    RecipeElementID = ET.SubElement(RecipeElement, "RecipeElementID")

    # build header child
    Header = ET.SubElement(RecipeElement,"Header")
    # build steps child
    Steps = ET.SubElement(RecipeElement,"Steps")

    # fill in header  child
    for child in root:
        if child.tag == '{urn:Rockwell/MasterRecipe}Header':
            for el in child:
                el.tag=re.sub('{[^>]+}', '', el.tag)
                element = ET.SubElement(Header,el.tag)
                element.text = el.text
                element.attrib = el.attrib
                if el.tag == 'Resource':
                    resource = el.text # assign resource unit to variable resource

    RecipeElementID.text = op_filename.strip(".oxml")

    # initial step
    init_element = ET.SubElement(Steps,"InitialStep")
    init_element.set('XPos','600')
    init_element.set('YPos','100')
    init_subelement = ET.SubElement(init_element,'Name')
    init_subelement.text = "INITIALSTEP:1"

    # ending step
    end_element = ET.SubElement(Steps,"TerminalStep")
    end_element.set('XPos','700')
    end_subelement = ET.SubElement(end_element,'Name')
    end_subelement.text = "TERMINALSTEP:1"

    # cycle through each operation in the array op_list
    for op in op_list:
        input_tree = ET.parse(op + '.oxml')
        root = input_tree.getroot()
        max_y = 0
        max_y_current = 0

        if debug == 1:
            print(str(op_counter) + " " + str(op_delta))
        for child in root:

            if child.tag == '{urn:Rockwell/MasterRecipe}Steps':
                for el in child:
                    if el.tag == '{urn:Rockwell/MasterRecipe}Step':
                        el.tag=re.sub('{[^>]+}', '', el.tag)
                        element = ET.SubElement(Steps,el.tag)
                        element.text = el.text
                        element.attrib = el.attrib
                        if int(element.attrib["YPos"]) > max_y:
                            max_y = int(element.attrib["YPos"])
                        element.attrib["YPos"] = str(int(element.attrib["YPos"])+op_delta)
                        if debug == 1:
                            print("added step at: " + str(int(element.attrib["YPos"])))
                        if int(element.attrib["YPos"]) > max_y_current:
                            max_y_current = int(element.attrib["YPos"])
                        for sub_el in el:
                            if sub_el.tag == '{urn:Rockwell/MasterRecipe}Name':
                                if len(instances) == 0:
                                        instances.append(sub_el.text.split(":"))
                                        instances_substitutions.append([op_counter,sub_el.text,sub_el.text])
                                else:
                                    check = 0
                                    for i in range (0,len(instances)):
                                        if sub_el.text.split(":")[0] in instances[i]:
                                            original_text = sub_el.text
                                            instances[i][1]=str(int(instances[i][1])+1)
                                            sub_el.text = instances[i][0]+":"+instances[i][1]
                                            check = 1
                                            instances_substitutions.append([op_counter,original_text,sub_el.text])
                                            break
                                    if check == 0:
                                        instances.append(sub_el.text.split(":"))
                                        instances_substitutions.append([op_counter,sub_el.text,sub_el.text])
                            sub_el.tag=re.sub('{[^>]+}', '', sub_el.tag)
                            sub_element = ET.SubElement(element,sub_el.tag)
                            sub_element.text = sub_el.text
                            sub_element.attrib = sub_el.attrib
                            for sub_sub_el in sub_el:
                                sub_sub_el.tag=re.sub('{[^>]+}', '', sub_sub_el.tag)
                                sub_sub_element = ET.SubElement(sub_element,sub_sub_el.tag)
                                sub_sub_element.text = sub_sub_el.text
                                sub_sub_element.attrib = sub_sub_el.attrib
                                for sub_sub_sub_el in sub_sub_el:
                                    sub_sub_sub_el.tag=re.sub('{[^>]+}', '', sub_sub_sub_el.tag)
                                    sub_sub_sub_element = ET.SubElement(sub_sub_element,sub_sub_sub_el.tag)
                                    sub_sub_sub_element.text = sub_sub_sub_el.text
                                    sub_sub_sub_element.attrib = sub_sub_sub_el.attrib

            if child.tag == '{urn:Rockwell/MasterRecipe}Transition':
                transition_counter += 1

        if debug == 1:
            print('operation: ' + str(op_counter) + ' filename: ' + op + ' contains ' + str(transition_counter) + ' transitions.')

        #### NULL step
        if op_counter < len(op_list)-1:
            null_element = ET.SubElement(Steps,"Step")
            null_element.set('SystemStep','$NULL')
            null_element.set('AcquireUnit','true')
            null_element.set('XPos','500')
            null_element.set('YPos',str(max_y_current+1200))
            null_subelement = ET.SubElement(null_element,'Name')

            if len(instances) == 0:
                instances.append(['$NULL','1'])
                null_subelement.text = "$NULL:1"
            else:
                check = 0
                for el in instances:
                    if el[0] == "$NULL":
                        el[1]=str(int(el[1])+1)
                        null_subelement.text = "$NULL:" + el[1]
                        check = 1
                        break
                if check == 0:
                    instances.append(['$NULL','1'])
                    null_subelement.text = "$NULL:1"

            null_instances.append(null_subelement.text)
            null_subelement = ET.SubElement(null_element,'StepRecipeID')
            null_subelement.text = "$NULL"
            null_subelement = ET.SubElement(null_element,'UnitAlias')
            null_subelement.text = resource

            if debug == 1:
                print("added NULL step at: " + str(max_y_current+1200))

        #### NULL step

        transition_index = 0

        for child in root:

            if child.tag == '{urn:Rockwell/MasterRecipe}Transition':

                if (((op_counter == 0) and (transition_index < transition_counter)) or
                   ((op_counter > 0) and (op_counter < len(op_list)-1) and (transition_index < transition_counter)) or
                   ((op_counter == len(op_list)-1))):

                    # print('operation:' + str(op_counter) + ' added transition at counter: ' + str(transition_index))
                    child.tag=re.sub('{[^>]+}', '', child.tag)
                    element = ET.SubElement(RecipeElement,child.tag)
                    element.text = child.text
                    element.attrib = child.attrib
                    if int(element.attrib["YPos"]) > max_y:
                            max_y = int(element.attrib["YPos"])
                    element.attrib["YPos"] = str(int(element.attrib["YPos"])+op_delta)
                    if debug == 1:
                        print("added transition at: " + str(int(element.attrib["YPos"])))
                    for sub_el in child:
                        if sub_el.tag == '{urn:Rockwell/MasterRecipe}Name':
                            original_t_text = sub_el.text
                            sub_el.text = "T" + str(transition_global)
                            transitions_substitutions.append([op_counter,original_t_text,sub_el.text])
                        if sub_el.tag == '{urn:Rockwell/MasterRecipe}ConditionalExpression':
                            for el in instances_substitutions:
                                if el[0] == op_counter and sub_el.text.find(el[1]) != -1:
                                    sub_el.text = sub_el.text.replace(el[1],el[2])
                                    break
                        sub_el.tag=re.sub('{[^>]+}', '', sub_el.tag)
                        sub_element = ET.SubElement(element,sub_el.tag)
                        sub_element.text = sub_el.text
                        sub_element.attrib = sub_el.attrib

                    transition_global += 1
                    transition_index += 1
                else:
                    transition_index += 1

        op_counter += 1             # next op in array
        transition_counter = 0      # reset counter for transition
        op_delta = op_delta + max_y + 600       # update pixel y coord delta value for next op

    op_counter = 0

    for op in op_list:
        input_tree = ET.parse(op + '.oxml')
        root = input_tree.getroot()
        link_index = 0

        for child in root:
            if child.tag == '{urn:Rockwell/MasterRecipe}ElementLink':
                link_counter += 1

        if debug == 1:
            print('operation: ' + str(op_counter) + ' contains ' + str(link_counter) + ' links.')

        for child in root:

            if child.tag == '{urn:Rockwell/MasterRecipe}ElementLink':

                if (((op_counter == 0) and (link_index < link_counter)) or
                   ((op_counter > 0) and (op_counter < len(op_list)-1) and (link_index < link_counter)) or
                   ((op_counter == len(op_list)-1))):

                    # print('operation:' + str(op_counter) + ' added link at counter: ' + str(link_index))
                    child.tag=re.sub('{[^>]+}', '', child.tag)
                    element = ET.SubElement(RecipeElement,child.tag)
                    element.text = child.text

                    for sub_el in child:
                        sub_el.tag=re.sub('{[^>]+}', '', sub_el.tag)
                        sub_element = ET.SubElement(element,sub_el.tag)

                        # substitutions
                        # cycle through arrays for substituions

                        for item in transitions_substitutions:
                            if (item[0] == op_counter and item[1] == sub_el.text):
                                sub_el.text = item[2]
                                break
                        for item in instances_substitutions:
                            if (item[0] == op_counter and item[1] == sub_el.text):
                                sub_el.text = item[2]
                                break

                        #
                        if (op_counter < len(op_list)-1 and sub_el.text == "TERMINALSTEP:1"):
                            sub_el.text = null_instances[op_counter]
                        if (op_counter > 0 and sub_el.text == "INITIALSTEP:1"):
                            sub_el.text = null_instances[op_counter-1]

                        sub_element.text = sub_el.text

                    link_global += 1
                    link_index += 1
                else:
                    link_index += 1

        op_counter += 1             # next op in array
        link_counter = 0            # reset counter for links

    # build unit req and comment child
    UnitRequirement = ET.SubElement(RecipeElement,"UnitRequirement")
    Comments = ET.SubElement(RecipeElement,"Comments")

    for child in root:
        if child.tag == '{urn:Rockwell/MasterRecipe}UnitRequirement':
            for el in child:
                el.tag=re.sub('{[^>]+}', '', el.tag)
                element = ET.SubElement(UnitRequirement,el.tag)
                element.text = el.text
                element.attrib = el.attrib

    # update ypos for TerminalStep
    end_element.set('YPos',str(op_delta + 600))

    ########################################################################################################################

    # write everything to file
    tree = ET.ElementTree(RecipeElement)
    print("Writing merged OP to disk...")
    tree.write(op_filename, encoding='utf-16', method='xml')

    # print some other info about xml mangling
    if debug == 1:
        print(transitions_substitutions)
        print(instances)

print("It's done. Now send me your money!")
