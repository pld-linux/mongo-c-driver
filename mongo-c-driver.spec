#
# Conditional build:
%bcond_with	tests	# build with tests
%bcond_without	doc	# HTML and man documentation
%bcond_with	sasl	# SASL authentication (for Kerberos)
%bcond_without	ssl	# TLS connections and SCRAM-SHA-1 authentication

# NOTE about arch:
# See https://jira.mongodb.org/browse/CDRIVER-1186
# 32-bit MongoDB support was officially deprecated
# in MongoDB 3.2, and support is being removed in 3.4.

Summary:	Client library written in C for MongoDB
Summary(pl.UTF-8):	Biblioteka kliencka do MongoDB napisana w C
Name:		mongo-c-driver
Version:	1.20.0
Release:	1
License:	Apache v2.0
Group:		Libraries
#Source0Download: https://github.com/mongodb/mongo-c-driver/releases/
Source0:	https://github.com/mongodb/mongo-c-driver/releases/download/%{version}/%{name}-%{version}.tar.gz
# Source0-md5:	9cd2badc1cea0a7943325ef18caef5c5
URL:		https://github.com/mongodb/mongo-c-driver
BuildRequires:	cmake >= 3.1
%{?with_sasl:BuildRequires:	cyrus-sasl-devel}
BuildRequires:	libicu-devel
%{?with_ssl:BuildRequires:	openssl-devel}
BuildRequires:	pkgconfig
BuildRequires:	python
BuildRequires:	snappy-devel
%{?with_doc:BuildRequires:	sphinx-pdg}
BuildRequires:	zlib-devel >= 1.2.11
BuildRequires:	zstd-devel
%if %{with tests}
BuildRequires:	mongodb-server
BuildRequires:	openssl
%endif
Requires:	%{name}-libs = %{version}-%{release}
Obsoletes:	mongo-c-driver-tools < 1.3.0
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		libver       1.0

%description
mongo-c-driver is a client library written in C for MongoDB.

%description -l pl.UTF-8
mongo-c-driver to biblioteka kliencka do MongoDB napisana w C.

%package libs
Summary:	Shared library for mongo-c-driver
Summary(pl.UTF-8):	Biblioteka współdzielona mongo-c-driver
Group:		Libraries
Requires:	libbson = %{version}-%{release}
Requires:	zlib >= 1.2.11

%description libs
This package contains the shared library for mongo-c-driver.

%description libs -l pl.UTF-8
Ten pakiet zawiera bibliotekę współdzieloną mongo-c-driver.

%package devel
Summary:	Header files for mongo-c-driver library
Summary(pl.UTF-8):	Pliki nagłówkowe biblioteki mongo-c-driver
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description devel
This package contains the header files for mongo-c-driver library.

Documentation: http://mongoc.org/libmongoc/%{version}/

%description devel -l pl.UTF-8
Ten pakiet zawiera pliki nagłówkowe biblioteki mongo-c-driver.

Dokumentacja: http://mongoc.org/libmongoc/%{version}/

%package apidocs
Summary:	API documentation for mongo-c-driver library
Summary(pl.UTF-8):	Dokumentacja API biblioteki mongo-c-driver
Group:		Documentation

%description apidocs
API documentation for mongo-c-driver library.

%description apidocs -l pl.UTF-8
Dokumentacja API biblioteki mongo-c-driver.

%package -n libbson
Summary:	Building, parsing, and iterating BSON documents
Summary(pl.UTF-8):	Tworzenie, analiza i przechodzenie dokumentów BSON
License:	Apache v2.0 and ISC and MIT and zlib
Group:		Libraries

%description -n libbson
This is a library providing useful routines related to building,
parsing, and iterating BSON documents <http://bsonspec.org/>.

%description -n libbson -l pl.UTF-8
Ta biblioteka udostępnia przydatne funkcje związane z budowaniem,
analizą i przechodzeniem dokumentów BSON (<http://bsonspec.org/>).

%package -n libbson-devel
Summary:	Development files for libbson
Summary(pl.UTF-8):	Pliki programistyczne biblioteki libbson
License:	Apache v2.0
Group:		Development/Libraries
Requires:	libbson = %{version}-%{release}

%description -n libbson-devel
This package contains libraries and header files needed for developing
applications that use libbson.

%description -n libbson-devel -l pl.UTF-8
Ten pakiet zawiera pliki nagłówkowe do tworzenia aplikacji
wykorzystujących bibliotekę libbson.

%package -n libbson-apidocs
Summary:	API documentation for libbson library
Summary(pl.UTF-8):	Dokumentacja API biblioteki libbson
Group:		Documentation

%description -n libbson-apidocs
API documentation for libbson library.

%description -n libbson-apidocs -l pl.UTF-8
Dokumentacja API biblioteki libbson.

%prep
%setup -q

%build
install -d cmake-build
cd cmake-build
%cmake \
	-DENABLE_AUTOMATIC_INIT_AND_CLEANUP=OFF \
	-DENABLE_BSON=ON \
	-DENABLE_EXAMPLES=ON \
	-DENABLE_HTML_DOCS=%{!?with_doc:OFF}%{?with_doc:ON} \
	-DENABLE_MAN_PAGES=%{!?with_doc:OFF}%{?with_doc:ON} \
	-DENABLE_SASL=%{!?with_sasl:OFF}%{?with_sasl:CYRUS} \
	-DENABLE_SHM_COUNTERS=ON \
	-DENABLE_SSL=%{!?with_ssl:OFF}%{?with_ssl:OPENSSL -DENABLE_CRYPTO_SYSTEM_PROFILE=ON} \
	-DENABLE_STATIC=OFF \
	-DENABLE_TESTS=%{!?with_tests:OFF}%{?with_tests:ON} \
	-DENABLE_ZLIB=SYSTEM \
	..

%{__make} -j1

%if %{with tests}
: Run a server
install -d dbtest
mongod \
	--journal \
	--ipv6 \
	--unixSocketPrefix /tmp \
	--logpath $PWD/server.log \
	--pidfilepath $PWD/server.pid \
	--dbpath $PWD/dbtest \
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

# packaged as %doc / unneeded in rpm
%{__rm} $RPM_BUILD_ROOT%{_datadir}/%{name}/{COPYING,NEWS,README.rst,THIRD_PARTY_NOTICES,uninstall.sh}
%if %{with doc}
%{__rm} -r $RPM_BUILD_ROOT%{_docdir}/{mongo-c-driver,libbson}/html
%endif

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
%doc NEWS README.rst THIRD_PARTY_NOTICES
%attr(755,root,root) %{_libdir}/libmongoc-%{libver}.so.*.*.*
%attr(755,root,root) %ghost %{_libdir}/libmongoc-%{libver}.so.0

%files devel
%defattr(644,root,root,755)
%attr(755,root,root) %{_libdir}/libmongoc-%{libver}.so
%{_includedir}/libmongoc-%{libver}
%{_pkgconfigdir}/libmongoc-%{libver}.pc
%{_pkgconfigdir}/libmongoc-ssl-%{libver}.pc
%{_libdir}/cmake/libmongoc-%{libver}
%{_libdir}/cmake/mongoc-*.*
%if %{with doc}
%{_mandir}/man3/mongoc_*.3*
%endif
%{_examplesdir}/libmongoc-%{version}

%if %{with doc}
%files apidocs
%defattr(644,root,root,755)
%doc cmake-build/src/libmongoc/doc/html/{_images,_static,*.html,*.js}
%endif

%files -n libbson
%defattr(644,root,root,755)
%doc src/libbson/{NEWS,THIRD_PARTY_NOTICES}
%attr(755,root,root) %{_libdir}/libbson-%{libver}.so.*.*.*
%attr(755,root,root) %ghost %{_libdir}/libbson-%{libver}.so.0

%files -n libbson-devel
%defattr(644,root,root,755)
%attr(755,root,root) %{_libdir}/libbson-%{libver}.so
%{_includedir}/libbson-%{libver}
%{_pkgconfigdir}/libbson-%{libver}.pc
%{_libdir}/cmake/bson-*.*
%{_libdir}/cmake/libbson-%{libver}
%if %{with doc}
%{_mandir}/man3/bson_*.3*
%endif
%{_examplesdir}/libbson-%{version}

%if %{with doc}
%files -n libbson-apidocs
%defattr(644,root,root,755)
%doc cmake-build/src/libbson/doc/html/{_static,*.html,*.js}
%endif
