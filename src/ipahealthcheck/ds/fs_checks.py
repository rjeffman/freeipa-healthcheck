#
# Copyright (C) 2020 FreeIPA Contributors see COPYING for license
#

import logging
from ipahealthcheck.core import constants
from ipahealthcheck.core.plugin import Result, duration
from ipahealthcheck.ds.plugin import DSPlugin, registry
from lib389.dseldif import FSChecks


@registry
class FSCheck(DSPlugin):
    """
    Check the FS for permissions issues impacting DS
    """
    requires = ('dirsrv',)

    @duration
    def check(self):
        results = self.doCheck(FSChecks)
        if len(results) > 0:
            for result in results:
                yield result
        else:
            yield Result(self, constants.SUCCESS)