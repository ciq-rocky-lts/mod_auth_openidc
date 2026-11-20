%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn || echo 0-0)}}
%{!?_httpd_moddir: %{expand: %%global _httpd_moddir %%{_libdir}/httpd/modules}}
%{!?_httpd_confdir: %{expand: %%global _httpd_confdir %{_sysconfdir}/httpd/conf.d}}

# Optionally build with hiredis if --with hiredis is passed
%{!?_with_hiredis: %{!?_without_hiredis: %global _without_hiredis --without-hiredis}}
# It is an error if both or neither required options exist.
%{?_with_hiredis: %{?_without_hiredis: %{error: both _with_hiredis and _without_hiredis}}}
%{!?_with_hiredis: %{!?_without_hiredis: %{error: neither _with_hiredis nor _without_hiredis}}}

# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}

%global httpd_pkg_cache_dir /var/cache/httpd/mod_auth_openidc

Name:		mod_auth_openidc
Version:	1.8.8
Release:	9.1%{?dist}
Summary:	OpenID Connect auth module for Apache HTTP Server

Group:		System Environment/Daemons
License:	ASL 2.0
URL:		https://github.com/pingidentity/mod_auth_openidc
Source0:	https://github.com/pingidentity/mod_auth_openidc/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

Patch0: decrypt_aesgcm.patch
Patch1: 0001-don-t-echo-query-params-on-invalid-requests-to-redir.patch
Patch2: 0002-Backport-security-fix-scrub-headers-on-OIDCUnAuthAct.patch
Patch3: 0003-Backport-security-fix-scrub-headers-for-AuthType-oau.patch
Patch4: 0004-Backport-of-improve-validation-of-the-post-logout-UR.patch
Patch5: 0005-Backport-of-Fix-open-redirect-starting-with-a-slash.patch
Patch6: 0006-Backport-of-Fix-open-redirect-starting-with-a-slash-.patch
Patch7: 0007-Fix-the-previous-backports.patch

# BZ1823762 - Backport SameSite=None cookie from mod_auth_openidc upstream
#             to support latest browsers [rhel-7.9.z]
Patch8:  0008-add-value-of-OIDC_SET_COOKIE_APPEND-env-var-to-Set-C.patch
Patch9:  0009-Backport-setting-an-extra-cookie-parameter.patch
Patch10: 0010-always-add-a-SameSite-Never-value-to-the-Set-Cookie-.patch
Patch11: 0011-Backport-of-fix-also-add-SameSite-None-to-by-value-s.patch
Patch12: 0012-Only-set-Same-Site-None-if-an-option-is-set.patch
# CVE-2026-54789 - adapted from github.com: https://github.com/OpenIDC/mod_auth_openidc/commit/8017478471cc071c49aa073c5c9be652a73a8630.patch (relative to the source it omits 12 changed lines)
Patch13: mod_auth_openidc-1.8.8-CVE-2026-54789.patch
# CVE-2024-24814: not applicable — NVD affected range is >= 2.0.0, < 2.4.15.2;
# 1.8.8 has no chunked-session-cookie code (introduced in 2.0.0)

BuildRequires:	httpd-devel
BuildRequires:	openssl-devel
BuildRequires:	curl-devel
BuildRequires:	jansson-devel
BuildRequires:	pcre-devel
BuildRequires:	autoconf
BuildRequires:	automake
%{?_with_hiresdis:BuildRequires: hiresdis-devel}
Requires:	httpd-mmn = %{_httpd_mmn}

%description
This module enables an Apache 2.x web server to operate as
an OpenID Connect Relying Party and/or OAuth 2.0 Resource Server.

%prep
%setup -q
%patch0 -p1 -b decrypt_aesgcm
%patch1 -p1 -b echo_req
%patch2 -p1 -b scrub_headers
%patch3 -p1 -b scrub_headers_oauth
%patch4 -p1 -b improve_logout_validation
%patch5 -p1 -b logout_slash
%patch6 -p1 -b logout_backslash
%patch7 -p1 -b logout_regression
%patch8 -p1 -b cookie_env_append
%patch9 -p1 -b cookie_ext_value
%patch10 -p1 -b same_site_none
%patch11 -p1 -b same_site_none_fix
%patch12 -p1 -b same_site_none_opt
%patch13 -p1 -b .CVE-2026-54789

%build
# workaround rpm-buildroot-usage
export MODULES_DIR=%{_httpd_moddir}
export APXS2_OPTS='-S LIBEXECDIR=${MODULES_DIR}'
autoreconf
%configure \
  %{?_with_hiredis} \
  %{?_without_hiredis}

make %{?_smp_mflags}

%check
export MODULES_DIR=%{_httpd_moddir}
make %{?_smp_mflags} test

%install
mkdir -p $RPM_BUILD_ROOT%{_httpd_moddir}
make install MODULES_DIR=$RPM_BUILD_ROOT%{_httpd_moddir}

install -m 755 -d $RPM_BUILD_ROOT%{_httpd_modconfdir}
echo 'LoadModule auth_openidc_module modules/mod_auth_openidc.so' > \
	$RPM_BUILD_ROOT%{_httpd_modconfdir}/10-auth_openidc.conf

install -m 755 -d $RPM_BUILD_ROOT%{_httpd_confdir}
install -m 644 auth_openidc.conf $RPM_BUILD_ROOT%{_httpd_confdir}
# Adjust httpd cache location in install config file
sed -i 's!/var/cache/apache2/!/var/cache/httpd/!' $RPM_BUILD_ROOT%{_httpd_confdir}/auth_openidc.conf
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}/metadata
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}/cache


%files
%if 0%{?rhel} && 0%{?rhel} < 7
%doc LICENSE.txt
%else
%license LICENSE.txt
%endif
%doc ChangeLog
%doc AUTHORS
%doc DISCLAIMER
%doc README.md
%{_httpd_moddir}/mod_auth_openidc.so
%config(noreplace) %{_httpd_modconfdir}/10-auth_openidc.conf
%config(noreplace) %{_httpd_confdir}/auth_openidc.conf
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}/metadata
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}/cache

%changelog
* Fri Sep 04 2026 Jason Rodriguez <jrodriguez@ciq.com> - 1.8.8-9.1
- Fix CVE-2026-54789
- CVE-2024-24814: not affected (NVD range >= 2.0.0; chunked-cookie code
  absent from 1.8.8)

* Thu Oct  8 2020 Jakub Hrozek <jhrozek@redhat.com> - 1.8.8-9
- Rebuild to pick up the proper build tag
- Related: rhbz#1823762 - Backport SameSite=None cookie from
                          mod_auth_openidc upstream to support
                          latest browsers [rhel-7.9.z]

* Wed Aug 26 2020 Jakub Hrozek <jhrozek@redhat.com> - 1.8.8-8
- Resolves: rhbz#1823762 - Backport SameSite=None cookie from
                           mod_auth_openidc upstream to support
                           latest browsers [rhel-7.9.z]

* Mon Mar 16 2020 Jakub Hrozek <jhrozek@redhat.com> - 1.8.8-7
- Fix a regression in the previous patches
- Related: rhbz#1805748 - CVE-2019-20479 mod_auth_openidc: open redirect
                          issue exists in URLs with slash and backslash [rhel-7]

* Mon Mar 16 2020 Jakub Hrozek <jhrozek@redhat.com> - 1.8.8-6
- Resolves: rhbz#1805748 - CVE-2019-20479 mod_auth_openidc: open redirect
                           issue exists in URLs with slash and backslash [rhel-7]
- Resolves: rhbz#1805067 - CVE-2019-14857 mod_auth_openidc: Open redirect
                           in logout url when using URLs with leading slashes
                           [rhel-7]

* Tue Jan 29 2019 Jakub Hrozek <jhrozek@redhat.com> - 1.8.8-5
- Resolves: rhbz#1626297 - CVE-2017-6413 mod_auth_openidc: OIDC_CLAIM and
                           OIDCAuthNHeader not skipped in an "AuthType oauth20"
                           configuration [rhel-7]

* Tue Jan 29 2019 Jakub Hrozek <jhrozek@redhat.com> - 1.8.8-4
- Resolves: rhbz#1626299 - CVE-2017-6059 mod_auth_openidc: Shows
                           user-supplied content on error pages [rhel-7]

* Thu Mar 31 2016 John Dennis <jdennis@redhat.com> - 1.8.8-3
- fix unit test failure caused by apr_jwe_decrypt_content_aesgcm()
  failing to null terminate decrypted string
  Resolves: bug#1292561 New package: mod_auth_openidc

* Tue Mar 29 2016 John Dennis <jdennis@redhat.com> - 1.8.8-2
- Add %check to run test
  Resolves: bug#1292561 New package: mod_auth_openidc

* Tue Mar 29 2016 John Dennis <jdennis@redhat.com> - 1.8.8-1
- Initial import
  Resolves: bug#1292561 New package: mod_auth_openidc

