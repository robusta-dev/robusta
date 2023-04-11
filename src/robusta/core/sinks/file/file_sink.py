import json
import sys
from robusta.core.reporting.base import Finding
from robusta.core.reporting.blocks import FileBlock
from robusta.core.sinks.file.file_sink_params import FileSinkConfigWrapper
from robusta.core.sinks.file.object_traverser import ObjectTraverser
from robusta.core.sinks.sink_base import SinkBase


class FileSink(SinkBase):
    def __init__(self, sink_config: FileSinkConfigWrapper, registry):
        super().__init__(sink_config.file_sink, registry)

        self.__to_dictionary = ObjectTraverser(exclude_types=[FileBlock],
                                               exclude_empty_parent=False,
                                               exclude_patterns=["^\.add_silence_url$", "^\.dirty$"],
                                               ).to_dictionary
        # TODO: check fromat parameter to support other serialization formats
        self.__serialize = lambda data: json.dumps(data, indent=2)

    def write_finding(self, finding: Finding, platform_enabled: bool):

        dict_data = self.__to_dictionary(finding)
        data = self.__serialize(dict_data)

        # write to console if file_name not provided
        fout = sys.stdout if self.params.file_name is None else open(self.params.file_name, "a")
        try:
            fout.write(data)
            fout.write("\n")
        finally:
            if fout != sys.stdout and fout is not None:
                fout.close()
