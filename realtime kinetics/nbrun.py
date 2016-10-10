# Copyright (c) 2015 Antonino Ingargiola
# License: MIT
"""
nbrun - Run an Jupyter/IPython notebook, optionally passing arguments.

USAGE
-----

Copy this file in the folder containing the master notebook used to
execute the other notebooks.
"""

import os
import time
from IPython.display import display, FileLink
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


def dict_to_code(mapping):
    """Convert input dict `mapping` to a string containing python code.

    Each key is the name of a variable and each value is
    the variable content. Each variable assignment is separated by
    a newline.

    Keys must be strings, and cannot start with a number (i.e. must be
    valid python identifiers). Values must be objects with a string
    representation (the result of repr(obj)) which is valid python code for
    re-creating the object.
    For examples, numbers, strings or list/tuple/dict
    of numbers and strings are allowed.

    Returns:
        A string containing the python code.
    """
    lines = ("{} = {}".format(key, repr(value))
             for key, value in mapping.items())
    return '\n'.join(lines)

def run_notebook(notebook_name, nb_suffix='-out', out_path='.', nb_kwargs=None,
                 insert_pos=1, timeout=3600, execute_kwargs=None):
    """Runs a notebook and saves the output in a new notebook.

    Executes a notebook, optionally passing "arguments" in a way roughly
    similar to passing arguments to a function.
    Notebook arguments are passed in a dictionary (`nb_kwargs`) which is
    converted to a string containing python code, then inserted in the notebook
    as a code cell. The code contains only assignments of variables which
    can be used to control the execution of a suitably written notebook. When
    calling a notebook, you need to know which arguments (variables) to pass.
    Differently from functions, no check on the input arguments is performed.
    The "notebook signature" is only informally declared in a conventional
    markdown cell at the beginning of the notebook.

    Arguments:
        notebook_name (string): name of the notebook to be executed.
        nb_suffix (string): suffix to append to the file name of the executed
            notebook.
        nb_kwargs (dict or None): If not None, this dict is converted to a
            string of python assignments with keys representing variables
            names and values variables content. This string is inserted as
            code-cell in the notebook to be executed.
        insert_pos (int): position of insertion of the code-cell containing
            the input arguments. Default is 1 (i.e. second cell). With this
            default, the input notebook can define, in the first cell, default
            values of input arguments (used when the notebook is executed
            with no arguments or through the Notebook GUI).
        timeout (int): timeout in seconds after which the execution is aborted.
        execute_kwargs (dict): additional arguments passed to
            `ExecutePreprocessor`.
        out_path (string): folder where to save the output notebook.
    """
    timestamp_cell = "**Executed:** %s\n\n**Duration:** %d seconds."
    if nb_kwargs is not None:
        header = '# Cell inserted during automated execution.'
        code = dict_to_code(nb_kwargs)
        code_cell = '\n'.join((header, code))

    nb_name_input = notebook_name + '.ipynb'
    nb_name_output = notebook_name + '%s.ipynb' % nb_suffix
    nb_name_output = os.path.join(out_path, nb_name_output)
    display(FileLink(nb_name_input))

    if execute_kwargs is None:
        execute_kwargs = {}
    ep = ExecutePreprocessor(timeout=timeout, **execute_kwargs)
    nb = nbformat.read(nb_name_input, as_version=4)
    if len(nb_kwargs) > 0:
        nb['cells'].insert(1, nbformat.v4.new_code_cell(code_cell))

    start_time = time.time()
    try:
        # Execute the notebook
        ep.preprocess(nb, {'metadata': {'path': './'}})
    except:
        # Execution failed, print a message then raise.
        msg = 'Error executing the notebook "%s".\n\n' % notebook_name
        msg += 'See notebook "%s" for the traceback.' % nb_name_output
        print(msg)
        raise
    else:
        # On successful execution, add timestamping cell
        duration = time.time() - start_time
        timestamp_cell = timestamp_cell % (time.ctime(start_time), duration)
        nb['cells'].insert(0, nbformat.v4.new_markdown_cell(timestamp_cell))
    finally:
        # Save the notebook even when it raises an error
        nbformat.write(nb, nb_name_output)
        display(FileLink(nb_name_output))
