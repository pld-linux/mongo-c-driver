#
# Conditional build:
%bcond_with	tests		# build with tests
%bcond_with	doc		# build docs

# NOTE about arch:
# See https://jira.mongodb.org/browse/CDRIVER-1186
# 32-bit MongoDB support was officially deprecated
# in MongoDB 3.2, and support is being removed in 3.4.

Summary:	Client library written in C for MongoDB
Name:		mongo-c-driver
Version:	1.8.1
Release:	0.1
License:	Apache v2.0
Group:		Libraries
Source0:	https://github.com/mongodb/mongo-c-driver/releases/download/%{version}/%{name}-%{version}.tar.gz
# Source0-md5:	52d54a4107a2da20c1a1b28bc1ff9d44
Patch0:		%{name}-rpm.patch
URL:		https://github.com/mongodb/mongo-c-driver
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	cyrus-sasl-devel
BuildRequires:	libbson-devel >= 1.8
BuildRequires:	libtool
BuildRequires:	openssl-devel
BuildRequires:	perl-base
BuildRequires:	pkgconfig
BuildRequires:	snappy-devel
BuildRequires:	zlib-devel
%if %{with tests}
BuildRequires:	mongodb-server
BuildRequires:	openssl
%endif
%if %{with doc}
BuildRequires:	python
BuildRequires:	sphinx-pdg
%endif
Requires:	%{name}-libs = %{version}-%{release}
Obsoletes:	mongo-c-driver-tools < 1.3.0
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		libver       1.0

%description
%{name} is a client library written in C for MongoDB.

%package libs
Summary:	Shared libraries for %{name}
Group:		Development/Libraries

%description libs
This package contains the shared libraries for %{name}.

%package devel
Summary:	Header files and development libraries for %{name}
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description devel
This package contains the header files and development libraries for
%{name}.

Documentation: http://api.mongodb.org/c/%{version}/

%prep
%setup -q -n %{name}-%{version}%{?prever:-dev}
%patch0 -p1

%build
%{__aclocal} -I build/autotools -I build/autotools/m4
%{__libtoolize}
%{__autoconf} --include=build/autotools
%{__automake}

export LIBS=-lpthread

%configure \
	--enable-debug-symbols \
	--enable-shm-counters \
	--disable-automatic-init-and-cleanup \
	--enable-crypto-system-profile \
	%{__enable_disable doc man-pages} \
	%{__enable_disable tests} \
	--enable-sasl \
	--enable-ssl \
	--with-libbson=system \
	--with-snappy=system \
	--with-zlib=system \
	--disable-html-docs \
	--enable-examples \

%if 0
# remove these after autofoo as files required by automake
#configure.ac:68: installing 'build/autotools/missing'
#configure.ac:81: error: required file 'src/snappy-1.1.3/snappy-stubs-public.h.in' not found
#configure.ac:81: error: required file 'src/zlib-1.2.11/zconf.h.in' not found
rm -rf src/snappy-*
rm -rf src/zlib-*
rm -rf src/libbson
%endif

%{__make} all V=1

# Explicit man target is needed for generating manual pages
%if %{with doc}
%{__make} doc/man V=1
%endif

%if %{with tests}
: Run a server
install -d dbtest
mongod \
	--journal \
	--ipv6 \
	--unixSocketPrefix /tmp \
	--logpath	 $PWD/server.log \
	--pidfilepath $PWD/server.pid \
	--dbpath	  $PWD/dbtest \
	--fork

: Run the test suite
ret=0
export MONGOC_TEST_OFFLINE=on
#export MONGOC_TEST_SKIP_SLOW=on

%{__make} check || ret=1

: Cleanup
[ -s server.pid ] && kill $(cat server.pid)

exit $ret
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

rm $RPM_BUILD_ROOT%{_libdir}/*.la

: install examples
for i in examples/*.c examples/*/*.c; do
	install -Dpm 644 $i $RPM_BUILD_ROOT%{_docdir}/%{name}/$i
done

: Rename documentation to match subpackage name
mv $RPM_BUILD_ROOT%{_docdir}/%{name} \
   $RPM_BUILD_ROOT%{_docdir}/%{name}-devel

%clean
rm -rf $RPM_BUILD_ROOT

%post   libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%files
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/mongoc-stat

%files libs
%defattr(644,root,root,755)
%doc THIRD_PARTY_NOTICES COPYING
%attr(755,root,root) %{_libdir}/libmongoc-%{libver}.so.*.*.*
%ghost %{_libdir}/libmongoc-%{libver}.so.0

%files devel
%defattr(644,root,root,755)
%{_docdir}/%{name}-devel
%{_includedir}/libmongoc-%{libver}
%{_libdir}/libmongoc-%{libver}.so
%{_pkgconfigdir}/libmongoc-*.pc
%{_libdir}/cmake/libmongoc-%{libver}
%if %{with doc}
%{_mandir}/man3/mongoc*
%endif
