#
# Copyright (C) 2019 FreeIPA Contributors see COPYING for license
#

from ipahealthcheck.core import config, constants
from ipahealthcheck.ipa.plugin import registry
from ipahealthcheck.ipa.certs import IPACertNSSTrust
from unittest.mock import patch
from util import capture_results, CAInstance, no_exceptions


class mock_CertDB:
    def __init__(self, trust):
        """A dict of nickname + NSSdb trust flags"""
        self.trust = trust

    def list_certs(self):
        return [(nickname, self.trust[nickname]) for nickname in self.trust]


def my_unparse_trust_flags(trust_flags):
    return trust_flags


# These tests make some assumptions about the order in which the
# results are returned.


@patch('ipaserver.install.cainstance.CAInstance')
@patch('ipaserver.install.certs.CertDB')
@patch('ipapython.certdb.unparse_trust_flags')
def test_trust_default_ok(mock_unparse_trust_flags,
                          mock_certdb, mock_cainstance):
    """Test what should be the standard case"""
    trust = {
        'ocspSigningCert cert-pki-ca': 'u,u,u',
        'subsystemCert cert-pki-ca': 'u,u,u',
        'auditSigningCert cert-pki-ca': 'u,u,Pu',
        'Server-Cert cert-pki-ca': 'u,u,u'
    }

    mock_cainstance.return_value = CAInstance()
    mock_certdb.return_value = mock_CertDB(trust)
    mock_unparse_trust_flags.side_effect = my_unparse_trust_flags

    framework = object()
    registry.initialize(framework)
    f = IPACertNSSTrust(registry)

    f.config = config.Config()
    results = capture_results(f)

    assert len(results) == 4

    for result in results.results:
        assert result.severity == constants.SUCCESS
        assert result.source == 'ipahealthcheck.ipa.certs'
        assert result.check == 'IPACertNSSTrust'
        assert 'cert-pki-ca' in result.kw.get('key')

    no_exceptions(results)


@patch('ipaserver.install.cainstance.CAInstance')
@patch('ipaserver.install.certs.CertDB')
@patch('ipapython.certdb.unparse_trust_flags')
def test_trust_ocsp_missing(mock_unparse_trust_flags,
                            mock_certdb, mock_cainstance):
    """Test a missing certificate"""
    trust = {
        'subsystemCert cert-pki-ca': 'u,u,u',
        'auditSigningCert cert-pki-ca': 'u,u,Pu',
        'Server-Cert cert-pki-ca': 'u,u,u'
    }

    mock_cainstance.return_value = CAInstance()
    mock_certdb.return_value = mock_CertDB(trust)
    mock_unparse_trust_flags.side_effect = my_unparse_trust_flags

    framework = object()
    registry.initialize(framework)
    f = IPACertNSSTrust(registry)

    f.config = config.Config()
    results = capture_results(f)

    # The check reports success for those that it found and are correct and
    # reports missing certs last.
    num = len(results.results) - 2
    for r in range(0, num):
        result = results.results[r]
        assert result.severity == constants.SUCCESS
        assert result.source == 'ipahealthcheck.ipa.certs'
        assert result.check == 'IPACertNSSTrust'
        assert 'cert-pki-ca' in result.kw.get('key')

    result = results.results[-1]

    assert result.severity == constants.ERROR
    assert result.source == 'ipahealthcheck.ipa.certs'
    assert result.check == 'IPACertNSSTrust'
    assert result.kw.get('key') == 'ocspSigningCert cert-pki-ca'
    assert result.kw.get('msg') == 'Certificate ocspSigningCert ' \
                                   'cert-pki-ca missing while verifying trust'
    assert len(results) == 4
    
    no_exceptions(results)


@patch('ipaserver.install.cainstance.CAInstance')
@patch('ipaserver.install.certs.CertDB')
@patch('ipapython.certdb.unparse_trust_flags')
def test_trust_bad(mock_unparse_trust_flags,
                   mock_certdb, mock_cainstance):
    """Test multiple unexpected trust flags"""
    trust = {
        'ocspSigningCert cert-pki-ca': 'u,u,u',
        'subsystemCert cert-pki-ca': 'X,u,u',
        'auditSigningCert cert-pki-ca': 'u,u,Pu',
        'Server-Cert cert-pki-ca': 'X,u,u'
    }

    mock_cainstance.return_value = CAInstance()
    mock_certdb.return_value = mock_CertDB(trust)
    mock_unparse_trust_flags.side_effect = my_unparse_trust_flags

    framework = object()
    registry.initialize(framework)
    f = IPACertNSSTrust(registry)

    f.config = config.Config()
    results = capture_results(f)

    result = results.results[1]

    assert result.severity == constants.ERROR
    assert result.source == 'ipahealthcheck.ipa.certs'
    assert result.check == 'IPACertNSSTrust'
    assert result.kw.get('key') == 'subsystemCert cert-pki-ca'
    assert result.kw.get('msg') == 'Incorrect NSS trust for ' \
                                   'subsystemCert cert-pki-ca. Got X,u,u ' \
                                   'expected u,u,u'

    result = results.results[3]

    assert result.severity == constants.ERROR
    assert result.source == 'ipahealthcheck.ipa.certs'
    assert result.check == 'IPACertNSSTrust'
    assert result.kw.get('key') == 'Server-Cert cert-pki-ca'
    assert result.kw.get('msg') == 'Incorrect NSS trust for ' \
                                   'Server-Cert cert-pki-ca. Got X,u,u ' \
                                   'expected u,u,u'

    assert len(results) == 4

    no_exceptions(results)


@patch('ipaserver.install.cainstance.CAInstance')
def test_trust_caless(mock_cainstance):
    """Nothing to check if the master is CALess"""

    mock_cainstance.return_value = CAInstance(False)

    framework = object()
    registry.initialize(framework)
    f = IPACertNSSTrust(registry)

    f.config = config.Config()
    results = capture_results(f)

    assert len(results) == 0
