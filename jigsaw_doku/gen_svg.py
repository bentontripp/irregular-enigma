s = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink"\
    xmlns:svgjs="http://svgjs.dev/svgjs" viewBox="0 0 1400 800" width="1400" height="800">\n\
    \t<g stroke-width="1" stroke="hsl(32, 1%, 1%)" fill="none" stroke-linecap="round">'
for x in range(0, 800, 10):
    if x % 3 == 0:
        s += '        <path d="M 0 {} H 1400 " stroke-width="2"></path>\n'.format(x)
    else:
        s += '        <path d="M 0 {} H 1400 "></path>\n'.format(x)
for y in range(0, 1400, 10):
    if y % 3 == 0:
        s += '        <path d="M {} 0 V 800 " stroke-width="2"></path>\n'.format(y)
    else:
        s += '        <path d="M {} 0 V 800 "></path>\n'.format(y)
s += '\t</g>\n</svg>'

with open('sudokuprinter/static/img/background.svg', 'w') as f:
    f.write(s)
    f.close()