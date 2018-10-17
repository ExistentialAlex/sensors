
class MultiObservation:

    def __init__(self):
        self.id = None
        self.featureOfInterestId = None
        self.multidatastreamId = None
        self.phenomenonTime = None
        self.results = None
        self.parameters = None

    def __str__(self):
        return """featureOfInterestId: {0}, multidatastreamId: {1}, 
        phenomenonTime: {2}, results: {3}, parameters: {4}; id: {5}""".format(self.featureOfInterestId,
                                                                    self.multidatastreamId,
                                                                    self.phenomenonTime,
                                                                    self.result,
                                                                    str(self.parameters),
                                                                    self.id)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.featureOfInterestId != other.featureOfInterestId:
            return False
        if self.multidatastreamId != other.multidatastreamId:
            return False
        if self.phenomenonTime != other.phenomenonTime:
            return False
        if self.results != other.results:
            return False
        if self.parameters != other.parameters:
            return False
        return True

    def set_parameters(self, **parameters):
        self.parameters = dict(parameters)

    def set_parameters_from_str(self, parameters):
        self.parameters = {}
        params = parameters.split(",")
        for p in params:
            try:
                (k, v) = p.split(':')
                self.parameters[k.strip('"')] = v.strip('"')
            except ValueError:
                # self.logger.error("set_parameters_from_json(): Unable to parse parameter {0}", p)
                # continue
                raise("set_parameters_from_json(): Unable to parse parameter {0}".\
                    format(p))

    def get_parameters_as_str(self):
        return ",".join(['"{k}":"{v}"'.format(k=e[0], v=e[1]) for e in list(self.parameters.items())])
