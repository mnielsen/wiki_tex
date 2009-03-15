"""wiki_tex converts LaTeX documents to a form that can be easily
imported into MediaWiki.  Useage is:

python wiki_tex.py filename

This loads filename.tex and converts it into a file or files that can
be used as input to a MediaWiki.  By default, the program parses
everything between \begin{document} and \end{document}, and puts the
output into filename0.wiki.  However, it also has an option to output
multiple files.  To invoke this option, simply insert the line:

%#break

into your LaTeX code wherever you want a new output.  This will
generate articles filename0.wiki, filename1.wiki, and so on.  It
starts conversion wherver the first occurrence of %#break is.

The program is very simple.  It's a quick and dirty kludge, intended
to ease the process of importing into MediaWiki, not a full-fledged
converter.  With that in mind, I hope it's useful.
"""

import sys

def get_latex_file(base_web_filename):
  latex_file = open(base_web_filename+".tex","r")
  source = latex_file.read()
  latex_file.close()
  return source

def remove_comments(source):
  for comments in range(source.count('%')):
    start = source.find('%')
    end = source.find("\n",start)
    source = source[:start]+source[end:]
  return source

def replace_labelled_item(source):
  for j in range(source.count("\item[")):
    location = source.find("\item[")
    source = source.replace("\item[","",1)
    final_location = source.find("]",location)
    text = source[location:final_location]
    source = source[:location]+"* \'\'"+text+source[final_location+1:]
  return source

def find_closing_bracket(string,location,right_bracket="}"):
  left_bracket = {"}":"{", "]":"["}[right_bracket]
  num_brackets = 1
  while num_brackets > 0:
    next_left = string.find(left_bracket,location+1)
    if next_left == -1: next_left = 1000000000
    next_right = string.find(right_bracket,location+1)
    if next_left < next_right:
      num_brackets=num_brackets+1
      location=next_left
    else:
      num_brackets=num_brackets-1
      location=next_right
  return location

def simple_replacements(source):
  # Quote replacements need to be done first, so they don't interfere with
  # later replacements.
  replacements = {"``":"\"",
                  "''":"\""}
  for string in replacements: source = source.replace(string,replacements[string])
  replacements = {"\\begin{quote}":"",
                  "\\end{quote}":"",
                  "---":"-",
                  "\\begin{itemize}":"",    
                  "\\end{itemize}":"",
                  "\\begin{enumerate}":"",
                  "\\end{enumerate}":"", 
                  "\\item":"*",
                  "\\begin{eqnarray}":"\n<math>",
                  "\\end{eqnarray}":"</math>\n",
                  "\\begin{equation}":"\n<math>",
                  "\\end{equation}":"</math>\n",
                  "\\begin{theorem}":"\'\'\'Theorem:\'\'\'",
                  "\\end{theorem}":"",
                  "\\begin{lemma}":"\'\'\'Lemma:\'\'\'",
                  "\\end{lemma}":"",
                  "\\begin{corollary}":"\'\'\'Corollary:\'\'\'",
                  "\\end{corollary}":"",
                  "\qed":"<strong>QED</strong>"
                  }
  for string in replacements: source = source.replace(string,replacements[string])
  return source

def bracketed_replacements(source):
  replacements = {"\\emph{":"\'\'",
                  "\\textbf{":"\'\'\'",
                  "\\chapter{":"==",
                  "\\chapter*{":"==",
                  "\\section{":"===",
                  "\\section*{":"===",
                  "\\subsection{":"====",
                  "\\subsection*{":"===="}
  for string in replacements:
    for j in range(source.count(string)):
      current_location = source.find(string)
      source = source.replace(string,replacements[string],1)
      right_bracket = find_closing_bracket(source,current_location)
      source = source[:right_bracket]+replacements[string]+source[right_bracket+1:]
  return source

def replace_dollar(source):
  while source.find("$$") != -1:
    source = source.replace("$$","\n<math>",1)
    source = source.replace("$$","</math>\n",1)
  while source.find("$") != -1:
    source = source.replace("$","<math>",1)
    source = source.replace("$","</math>",1)
  return source

def replace_link(source):
  for j in range(source.count("\href{")):
    current_location = source.find("\href{")
    source = source.replace("\href{","",1)
    right_bracket = find_closing_bracket(source,current_location)
    url = source[current_location:right_bracket]
    url = url.replace("\_","_")
    url = url.replace("\#","#")
    url = url.replace("\&","&")
    second_right_bracket = find_closing_bracket(source,right_bracket+1)
    anchor = source[right_bracket+2:second_right_bracket]
    source = source[:current_location]+"<a href=\""+url+"\">"+anchor+"</a>"+source[second_right_bracket+1:]
  return source

def strip_lines(string):
  location = 0
  while string.find("\n",location) != -1:
    location = string.find("\n",location)
    if string.find("\n\n",location) != location:
      string = string[:location]+string[location+1:]
    else:
      location = location+4
  return string

def extract_article(source,article_number,num_articles,base_web_filename):
  source = remove_comments(source)
  source = simple_replacements(source)
  source = replace_labelled_item(source)
  source = bracketed_replacements(source)
  source = replace_dollar(source)
  source = replace_link(source)
  source = source.strip("\n")
  source = source.replace("\n\n\n","\n\n")
  source = strip_lines(source)
  print "Creating article number %s." % article_number
  article_file = open(base_web_filename+str(article_number)+".wiki",'w')
  article_file.write(source)
  article_file.close()

base_web_filename = sys.argv[1]
source = get_latex_file(base_web_filename)
source = source.replace("\\end{document}","")
num_articles = source.count('%#break')
print num_articles
if num_articles == 0:
  num_articles = 1
  source = source.replace("\\begin{document}",'%#break',1)

for article_number in range(num_articles):
  source = source[(source.find('%#break')+8):]
  if (article_number+1) < num_articles: article_source = source[0:source.find('%#break')]
  else: article_source = source
  extract_article(article_source,article_number,num_articles,base_web_filename)
