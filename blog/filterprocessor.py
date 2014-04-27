import markdown, re

class FilterProcessor:
    summary_start = 0
    summary_end = 1000
    tags = {'figure': self.figure, 'summary': self.summary}
    
    def __init__(self, md):
        self.source = md
        
    def run(self):
        filter_re = re.compile(r'\{(?P<tag_name>[a-zA-Z0-9\-_]+)\|(?P<attributes>.*?)\}')
        
        tokens = []
        pos = 0
        for m in filter_re.finditer(self.source):
            tokens.append(("literal", source[pos:m.start()]))
            tokens.append(("tag", m.group('tag_name'), m.group('attributes')))
            pos = m.end()
            
        if(pos < len(self.source)):
            tokens.append(("literal", source[pos:]))
            
        self.output = ""
        for token in tokens:
            if(token[0] == "literal"):
                self.output += token[1]
            else:
                kw = attributes_to_dict(token[2])
                self.tags[token[1]](**kw)
                
    
    def tag_figure(self, name=None, ref=None, thumbnail=True, title=True, comment=True):
        if name:
            """ This is a request to insert a named figure """
            fig = Figure.objects.get(label=name)
            self.output += self.figure_template.render(Context({"figure": fig,
                                                                "thumbnail": thumbnail,
                                                                "title": title,
                                                                "comment": comment}))
        else:
            """ This is a request to link to a named figure within this page """
            pass
        
    def tag_summary(self, start=False, end=False):
        if start:
            self.summary_start = len(self.output)
        if end:
            self.summary_end = len(self.output)
            