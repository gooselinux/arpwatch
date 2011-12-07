%define _vararpwatch %{_localstatedir}/lib/arpwatch

Name: arpwatch
Epoch: 14
Version: 2.1a15
Release: 14%{?dist}
Summary: Network monitoring tools for tracking IP addresses on a network
Group: Applications/System
License: BSD with advertising
URL: http://ee.lbl.gov/
Requires(pre): shadow-utils 
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig /sbin/service
Requires(postun): /sbin/service
Requires: /usr/sbin/sendmail
BuildRequires: /usr/sbin/sendmail libpcap-devel
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Source0: ftp://ftp.ee.lbl.gov/arpwatch-%{version}.tar.gz
Source1: arpwatch.init
Source2: arpwatch.sysconfig
# created by:
# wget -O- http://standards.ieee.org/regauth/oui/oui.txt | \
# iconv -f iso8859-1 -t utf8 | massagevendor | bzip2
Source3: ethercodes-20100330.dat.bz2
Patch1: arpwatch-2.1a4-fhs.patch
Patch2: arpwatch-2.1a10-man.patch
Patch3: arpwatch-drop.patch
Patch4: arpwatch-drop-man.patch
Patch5: arpwatch-addr.patch
Patch6: arpwatch-dir-man.patch
Patch7: arpwatch-scripts.patch
Patch8: arpwatch-2.1a15-nolocalpcap.patch
Patch9: arpwatch-2.1a15-bogon.patch
Patch10: arpwatch-2.1a15-extraman.patch

%description
The arpwatch package contains arpwatch and arpsnmp.  Arpwatch and
arpsnmp are both network monitoring tools.  Both utilities monitor
Ethernet or FDDI network traffic and build databases of Ethernet/IP
address pairs, and can report certain changes via email.

Install the arpwatch package if you need networking monitoring devices
which will automatically keep track of the IP addresses on your
network.

%prep
%setup -q

%patch1 -p1 -b .fhs
%patch2 -p1 -b .arpsnmpman
%patch3 -p1 -b .droproot
%patch4 -p0 -b .droprootman
%patch5 -p1 -b .mailuser
%patch6 -p1 -b .dirman
%patch7 -p1 -b .scripts
%patch8 -p1 -b .nolocalpcap
%patch9 -p1 -b .bogon
%patch10 -p1 -b .extraman

%build
%configure
make ARPDIR=%{_vararpwatch}

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT%{_mandir}/man8
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
mkdir -p $RPM_BUILD_ROOT%{_vararpwatch}
mkdir -p $RPM_BUILD_ROOT%{_initrddir}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig

make DESTDIR=$RPM_BUILD_ROOT install install-man

# prepare awk scripts
perl -pi -e "s/\'/\'\\\'\'/g" *.awk

# and embed them
for i in arp2ethers massagevendor massagevendor-old; do
	cp -f $i $RPM_BUILD_ROOT%{_sbindir}
	for j in *.awk; do
		sed "s/-f\ *\(\<$j\>\)/\'\1\n\' /g" \
			< $RPM_BUILD_ROOT%{_sbindir}/$i \
			| sed "s/$j\$//;tx;b;:x;r$j" \
			> $RPM_BUILD_ROOT%{_sbindir}/$i.x
		mv -f $RPM_BUILD_ROOT%{_sbindir}/$i{.x,}
	done
	chmod 755 $RPM_BUILD_ROOT%{_sbindir}/$i
done

install -p -m644 *.dat $RPM_BUILD_ROOT%{_vararpwatch}
install -p -m755 %{SOURCE1} $RPM_BUILD_ROOT%{_initrddir}/arpwatch
install -p -m644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/arpwatch
install -p -m644 %{SOURCE3} $RPM_BUILD_ROOT%{_vararpwatch}/ethercodes.dat.bz2
bzip2 -df $RPM_BUILD_ROOT%{_vararpwatch}/ethercodes.dat.bz2

rm -f $RPM_BUILD_ROOT%{_sbindir}/massagevendor-old

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add arpwatch

%pre
if ! getent group arpwatch &> /dev/null; then
	getent group pcap 2> /dev/null | grep -q 77 &&
		/usr/sbin/groupmod -n arpwatch pcap 2> /dev/null ||
		/usr/sbin/groupadd -g 77 arpwatch 2> /dev/null
fi
if ! getent passwd arpwatch &> /dev/null; then
	getent passwd pcap 2> /dev/null | grep -q 77 &&
		/usr/sbin/usermod -l arpwatch -g 77 \
			-d %{_vararpwatch} pcap 2> /dev/null ||
		/usr/sbin/useradd -u 77 -g 77 -s /sbin/nologin \
			-M -r -d %{_vararpwatch} arpwatch 2> /dev/null
fi
:

%postun
if [ "$1" -ge 1 ]; then
	/sbin/service arpwatch condrestart &> /dev/null
fi
:

%preun
if [ "$1" -eq 0 ]; then
	/sbin/service arpwatch stop &> /dev/null
	/sbin/chkconfig --del arpwatch
fi
:

%files
%defattr(-,root,root)
%doc README CHANGES arpfetch
%{_sbindir}/arpwatch
%{_sbindir}/arpsnmp
%{_sbindir}/arp2ethers
%{_sbindir}/massagevendor
%{_mandir}/man8/*.8*
%{_initrddir}/arpwatch
%config(noreplace) %{_sysconfdir}/sysconfig/arpwatch
%defattr(-,arpwatch,arpwatch)
%dir %{_vararpwatch}
%verify(not md5 size mtime) %config(noreplace) %{_vararpwatch}/arp.dat
%verify(not md5 size mtime) %config(noreplace) %{_vararpwatch}/ethercodes.dat

%changelog
* Tue Mar 30 2010 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-14
- update ethercodes.dat
- mark ethercodes.dat as noreplace
- include Debian arp2ethers and massagevendor man pages (#578201)
- don't include massagevendor-old script anymore

* Fri Jan 22 2010 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-13
- fix init script LSB compliance (#536823)

* Wed Sep 02 2009 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-12
- update ethercodes.dat

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 14:2.1a15-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 14:2.1a15-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Sep 16 2008 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-9
- update ethercodes.dat (#462364)

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 14:2.1a15-8
- Autorebuild for GCC 4.3

* Wed Aug 22 2007 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-7
- rebuild

* Thu Aug 09 2007 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-6
- improve init script (#246869)
- allow -n 0/32 to disable reporting bogons from 0.0.0.0 (#244606)
- update license tag
- update ethercodes.dat

* Wed Jun 13 2007 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-5
- update ethercodes.dat

* Thu May 24 2007 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-4
- fix return codes in init script (#237781)

* Mon Jan 15 2007 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-3
- rename pcap user to arpwatch

* Tue Nov 28 2006 Miroslav Lichvar <mlichvar@redhat.com> 14:2.1a15-2
- split from tcpdump package (#193657)
- update to 2.1a15
- clean up files in /var
- force linking with system libpcap
