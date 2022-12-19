class Annotation:

    def __init__(self,pos_x,pos_y,time_start,time_finish,match,match_date,annotator_name,action_type,description):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.time_start = time_start
        self.time_finish = time_finish
        self.match = match
        self.match_date = match_date
        self.annotator_name = annotator_name
        self.action_type = action_type
        self.description = description

    def __repr__(self):
        return "Annotation('{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(self.pos_x,self.pos_y,
                self.time_start,self.time_finish,self.match,self.match_date,self.annotator_name,self.action_type,
                self.description)