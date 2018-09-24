#
# Conditional build:
%bcond_with	tests		# build with tests
%bcond_with	doc		# build docs
%bcond_with	sasl		# Use libsasl for Kerberos.
%bcond_without	ssl		# Enable TLS connections and SCRAM-SHA-1 authentication.

# NOTE about arch:
# See https://jira.mongodb.org/browse/CDRIVER-1186
# 32-bit MongoDB support was officially deprecated
# in MongoDB 3.2, and support is being removed in 3.4.

Summary:	Client library written in C for MongoDB
Name:		mongo-c-driver
Version:	1.11.0
Release:	1
License:	Apache v2.0
Group:		Libraries
Source0:	https://github.com/mongodb/mongo-c-driver/releases/download/%{version}/%{name}-%{version}.tar.gz
# Source0-md5:	a1241743ac6c528df0b345560dfd07eb
URL:		https://github.com/mongodb/mongo-c-driver
BuildRequires:	cmake
%{?with_sasl:BuildRequires:	cyrus-sasl-devel}
%{?with_ssl:BuildRequires:	openssl-devel}
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
mongo-c-driver is a client library written in C for MongoDB.

%package libs
Summary:	Shared libraries for %{name}
Group:		Development/Libraries
Requires:	libbson = %{version}-%{release}

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

%package -n libbson
Summary:	Building, parsing, and iterating BSON documents
License:	ASL 2.0 and ISC and MIT and zlib
Group:		Libraries

%description -n libbson
This is a library providing useful routines related to building,
parsing, and iterating BSON documents <http://bsonspec.org/>.

%package -n libbson-devel
Summary:	Development files for libbson
License:	Apache v2.0
Group:		Development/Libraries
Requires:	libbson = %{version}-%{release}

%description -n libbson-devel
This package contains libraries and header files needed for developing
applications that use libbson.

%prep
%setup -q

%build
install -d cmake-build
cd cmake-build
%cmake \
	-DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF \
	-DENABLE_EXAMPLES=ON \
	-DENABLE_HTML_DOCS=OFF \
	-DENABLE_MAN_PAGES=%{!?with_doc:OFF}%{?with_doc:ON} \
	-DENABLE_SASL=%{!?with_sasl:OFF}%{?with_sasl:ON} \
	-DENABLE_SHM_COUNTERS=ON \
	-DENABLE_SSL=%{!?with_ssl:OFF}%{?with_ssl:OPENSSL -DENABLE_CRYPTO_SYSTEM_PROFILE=ON} \
	-DENABLE_STATIC=OFF \
	-DENABLE_TESTS=%{!?with_tests:OFF}%{?with_tests:ON} \
	..

%{__make}

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
%{__make} -C cmake-build install \
	DESTDIR=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{_examplesdir}/libmongoc-%{version}
cp -a src/libmongoc/examples/* $RPM_BUILD_ROOT%{_examplesdir}/libmongoc-%{version}

install -d $RPM_BUILD_ROOT%{_examplesdir}/libbson-%{version}
cp -a src/libbson/examples/* $RPM_BUILD_ROOT%{_examplesdir}/libbson-%{version}

%clean
rm -rf $RPM_BUILD_ROOT

%post   libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig

%post   -n libbson -p /sbin/ldconfig
%postun -n libbson -p /sbin/ldconfig

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
%doc NEWS
%{_includedir}/libmongoc-%{libver}
%{_libdir}/libmongoc-%{libver}.so
%{_pkgconfigdir}/libmongoc-*.pc
%{_libdir}/cmake/libmongoc-%{libver}
%if %{with doc}
%{_mandir}/man3/mongoc*
%endif
%{_examplesdir}/libmongoc-%{version}

%files -n libbson
%defattr(644,root,root,755)
%doc COPYING THIRD_PARTY_NOTICES
%attr(755,root,root) %{_libdir}/libbson-%{libver}.so.*.*.*
%ghost %{_libdir}/libbson-%{libver}.so.0

%files -n libbson-devel
%defattr(644,root,root,755)
%doc src/libbson/NEWS
%{_includedir}/libbson-%{libver}
%{_libdir}/libbson-%{libver}.so
%{_libdir}/cmake/libbson-%{libver}
%{_pkgconfigdir}/libbson-%{libver}.pc
%{_examplesdir}/libbson-%{version}
