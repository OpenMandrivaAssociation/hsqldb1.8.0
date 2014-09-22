%define _localstatedir %{_var}
%define section	devel
%define cvsver 	1_8_1_3
%define oname 	hsqldb

Summary:	Hsqldb Database Engine
Name:		hsqldb1.8.0
Version:	1.8.1.3
Release:	1
Group:		Development/Java
License:	BSD
Url:		http://hsqldb.sourceforge.net/
Source0:	http://downloads.sourceforge.net/hsqldb/hsqldb_%{cvsver}.zip
Source1:	hsqldb-1.8.0-standard.cfg
Source2:	hsqldb-1.8.0-standard-server.properties
Source3:	hsqldb-1.8.0-standard-webserver.properties
Source4:	hsqldb-1.8.0-standard-sqltool.rc
Patch0:		hsqldb-1.8.0-scripts.patch
Patch1:		hsqldb-tmp.patch
Patch2:		hsqldb-jdbc-4.1.patch
Buildarch:	noarch
BuildRequires:	java-1.7.0-devel
BuildRequires:	ant
BuildRequires:	junit
BuildRequires:	java-rpmbuild >= 0:1.5
BuildRequires:	tomcat-servlet-3.0-api
Requires(pre,post,preun,postun):	rpm-helper
Requires:	tomcat-servlet-3.0-api
Requires(post):	tomcat-servlet-3.0-api
Requires(post):	jpackage-utils
Requires(pre):	shadow-utils

%description
This package contains the hsqldb java classes. The server is contained
in the package %{oname}-server.

%package manual
Summary:	Manual for %{oname}
Group:		Development/Java

%description manual
Documentation for %{oname}.

%package javadoc
Summary:	Javadoc for %{oname}
Group:		Development/Java

%description javadoc
Javadoc for %{oname}.

%package demo
Summary:	Demo for %{oname}
Group:		Development/Java
Requires:	%{name} = %{version}-%{release}

%description demo
Demonstrations and samples for %{oname}.

%package server
Summary:	Hsqldb database server
Group:		System/Servers
Requires:	%{name} = %{version}-%{release}

%description server
HSQLdb is a relational database engine written in JavaTM , with a JDBC
driver, supporting a subset of ANSI-92 SQL. It offers a small (about
100k), fast database engine which offers both in memory and disk based
tables. Embedded and server modes are available. Additionally, it
includes tools such as a minimal web server, in-memory query and
management tools (can be run as applets or servlets, too) and a number
of demonstration examples.
Downloaded code should be regarded as being of production quality. The
product is currently being used as a database and persistence engine in
many Open Source Software projects and even in commercial projects and
products! In it's current version it is extremely stable and reliable.
It is best known for its small size, ability to execute completely in
memory and its speed. Yet it is a completely functional relational
database management system that is completely free under the Modified
BSD License. Yes, that's right, completely free of cost or restrictions!

This package contains the server.

%prep
%setup -T -c -n %{oname}
(cd ..
unzip -q %{SOURCE0} 
)
# set right permissions
find . -name "*.sh" -exec chmod 755 \{\} \;
# remove all _notes directories
for dir in `find . -name _notes`; do rm -rf $dir; done
# remove all binary libs
find . -name "*.jar" -exec rm -f {} \;
find . -name "*.class" -exec rm -f {} \;
find . -name "*.war" -exec rm -f {} \;
# correct silly permissions
chmod -R go=u-w *
%{_bindir}/find . -type f -name '*.css' -o -name '*.html' -o -name '*.txt' | \
  %{_bindir}/xargs -t perl -pi -e 's/\r$//g'

%apply_patches

cat > README.%{version}-%{release}.upgrade.urpmi <<EOF
The server has been removed from the hsqldb package and moved to a
separate package named %{oname}-server as it is not needed by most users.
Install it if you wish to use the Hsqldb server.
EOF

%build
export CLASSPATH=$(build-classpath \
	jsse/jsse \
	jsse/jnet \
	jsse/jcert \
	jdbc-stdext \
	servletapi5 \
	junit)
pushd build
ant jar javadoc
popd

%install
# jar
install -d -m 755 %{buildroot}%{_javadir}
install -m 644 lib/%{oname}.jar %{buildroot}%{_javadir}/%{oname}-%{version}.jar
(cd %{buildroot}%{_javadir} && for jar in *-%{version}.jar; do ln -sf ${jar} ${jar/-%{version}/}; done)
# bin
install -d -m 755 %{buildroot}%{_bindir}
install -m 755 bin/runUtil.sh %{buildroot}%{_bindir}/%{oname}RunUtil
# sysv init
install -d -m 755 %{buildroot}%{_initrddir}
install -m 755 bin/%{oname} %{buildroot}%{_initrddir}/%{oname}
# config
install -d -m 755 %{buildroot}%{_sysconfdir}/sysconfig
install -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/sysconfig/%{oname}
# serverconfig
install -d -m 755 %{buildroot}%{_localstatedir}/lib/%{oname}
install -m 644 %{SOURCE2} %{buildroot}%{_localstatedir}/lib/%{oname}/server.properties
install -m 644 %{SOURCE3} %{buildroot}%{_localstatedir}/lib/%{oname}/webserver.properties
install -m 600 %{SOURCE4} %{buildroot}%{_localstatedir}/lib/%{oname}/sqltool.rc
# lib
install -d -m 755 %{buildroot}%{_localstatedir}/lib/%{oname}/lib
install -m 644 lib/functions         %{buildroot}%{_localstatedir}/lib/%{oname}/lib
# data
install -d -m 755 %{buildroot}%{_localstatedir}/lib/%{oname}/data
# demo
install -d -m 755 %{buildroot}%{_datadir}/%{oname}/demo
install -m 755 demo/*.sh         %{buildroot}%{_datadir}/%{oname}/demo
install -m 644 demo/*.html         %{buildroot}%{_datadir}/%{oname}/demo
# javadoc
install -d -m 755 %{buildroot}%{_javadocdir}/%{oname}-%{version}
cp -r doc/src/* %{buildroot}%{_javadocdir}/%{oname}-%{version}
rm -rf doc/src
# manual
install -d -m 755 %{buildroot}%{_docdir}/%{oname}-%{version}
cp -r doc/* %{buildroot}%{_docdir}/%{oname}-%{version}
cp index.html %{buildroot}%{_docdir}/%{oname}-%{version}

%pre server
# Add the "hsqldb" user and group
# we need a shell to be able to use su - later

# (Anssi 01/2008) Previously _pre_groupadd was used here together with
# _pre_useradd, causing an error situation where group is created, but
# the user is not:
#    useradd:	group hsqldb exists - if you want to add this user to that group, use -g.
# Therefore we remove the hsqldb group if it exists without the corresponding
# user.
getent group %{oname} >/dev/null && ! getent passwd %{oname} >/dev/null && groupdel %{oname}  >/dev/null
getent passwd %{oname} >/dev/null && chsh -s /bin/sh %{oname} >/dev/null
%_pre_useradd %{oname} %{_localstatedir}/lib/%{oname} /bin/sh

%post server
rm -f %{_localstatedir}/lib/%{oname}/lib/hsqldb.jar
rm -f %{_localstatedir}/lib/%{oname}/lib/servlet.jar
(cd %{_localstatedir}/lib/%{oname}/lib
    ln -s %{_javadir}/hsqldb.jar hsqldb.jar
    ln -s %{_javadir}/servletapi5.jar servlet.jar
)
%_post_service %{name}

%postun server
%_postun_userdel %{oname}

%preun server
if [ "$1" = "0" ]; then
    rm -f %{_localstatedir}/lib/%{oname}/lib/hsqldb.jar
    rm -f %{_localstatedir}/lib/%{oname}/lib/servlet.jar
%if 0
    %{_sbindir}/userdel %{oname} >> /dev/null 2>&1 || :
    %{_sbindir}/groupdel %{oname} >> /dev/null 2>&1 || :
%endif
fi
%_preun_service %{name}

%files
%doc README*.urpmi
%{_javadir}/*

%files server
%{_bindir}/*
%{_initrddir}/%{oname}
%config(noreplace) %attr(0644,root,root) %{_sysconfdir}/sysconfig/%{oname}
%attr(0755,hsqldb,hsqldb) %{_localstatedir}/lib/%{oname}/data
%{_localstatedir}/lib/%{oname}/lib
%{_localstatedir}/lib/%{oname}/server.properties
%{_localstatedir}/lib/%{oname}/webserver.properties
%attr(0600,hsqldb,hsqldb) %{_localstatedir}/lib/%{oname}/sqltool.rc
%dir %{_localstatedir}/lib/%{oname}

%files manual
%doc %{_docdir}/%{oname}-%{version}

%files javadoc
%{_javadocdir}/%{oname}-%{version}

%files demo
%{_datadir}/%{oname}

