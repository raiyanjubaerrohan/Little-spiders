

liner = ''

while True:
    text = input(">>>")

    if text == "#exit": break

    liner += text
    
    if ';' in text:
    
        liner = liner.replace(';','')
        
        build(liner)
        liner = ""

