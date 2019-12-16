import glob

span_code = open('span.html').read()
html_pages = glob.glob('./**/*html', recursive=True)

for i in html_pages:
    f = open(i, 'r')
    alltext = f.readlines()
    f.close()
    if not 'version_switch' in alltext:
        for index, line in enumerate(alltext):
            if 'sphinxsidebarwrapper' in line:
                alltext.insert(index+1, span_code)
            if r'</head>' in line:
                headline = index
        alltext.insert(headline-1, '<script src="/_static/js/version.js"></script>')
        f = open(i, 'w')
        f.write("".join(alltext))
        f.close()
