%define toopherconfdir %{_sysconfdir}/security/toopher
%define __os_install_post %{nil} # Don't strip them binaries!

Name:		pam_toopher
Version:	%{autoconfversion}
Release:	1%{?dist}
Summary:	PAModule providing Toopher's strong authentication

Group:		System Environment/Base
License:	EPL+MIT
URL:		http://www.toopher.com
Source0:	%{distarchives}
Patch:		pam_toopher-add-pamconf
BuildRoot:	%{_tmppath}/%{name}-%{version}-build
BuildRequires:	pam-devel
BuildRequires:	python-devel

Requires(pre):	shadow-utils
Requires:	python


%description
This package provides a PAModule that allows Toopher to be used for
authentication by any program supporting PAM.

%prep
%setup -n toopher-pam-%{version}
%patch -p1

%build
user=$(whoami)
%configure --with-admin-group=$user
make

%pre
getent group toopher-admin >/dev/null || groupadd -r toopher-admin

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
install -d %{buildroot}/etc/pam.d
install password+toopher-auth %{buildroot}/etc/pam.d/
install -d %{buildroot}/etc/prelink.conf.d
echo '-b /usr/bin/toopher-pair' >> %{buildroot}/etc/prelink.conf.d/%{name}.conf
echo '-b /usr/bin/toopher-api-helper' >> %{buildroot}/etc/prelink.conf.d/%{name}.conf

%clean
rm -rf %{buildroot}


%files
%defattr(-, root, root)
%dir %{toopherconfdir}
%config(noreplace) %{toopherconfdir}/config
%config(noreplace) %attr(640, root, toopher-admin) %{toopherconfdir}/credentials
%config(noreplace) %attr(644, root, root) /etc/pam.d/password+toopher-auth
/%{_lib}/security/pam_toopher.so
%attr(2755, root, toopher-admin) %{_bindir}/toopher-api-helper
%{_bindir}/toopher-pair
%{_sysconfdir}/prelink.conf.d/%{name}.conf

%changelog

