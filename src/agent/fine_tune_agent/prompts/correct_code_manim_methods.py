correct_code_manim_methods = '''
you are an expert developer in python, who understands the manim docs very well.
the error of manim - {sandbox_error}
and the code is - {code}

you have to analyze the issue in the exact lines of code where the issue is, 
if its an incorrect method usage issue then use manim docs for that to use correct manim primitives
docs - {manim_docs}

if its python syntax issue then fix that accordingly.
if the issue is related to any library not found such as latex issues then try to edit the code of parts whose dependency is on latex.

#constraints
make sure to only edit the code so that it can run, do not change the meaning of code or any logic until and unless explicitly required.

you have to output the correct code.

'''