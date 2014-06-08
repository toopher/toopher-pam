#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_INIT([toopher-pam], [1.1.0], [dev@toopher.com])
AC_CONFIG_AUX_DIR([build-aux])
AC_CONFIG_MACRO_DIR([m4])
LT_INIT
LT_SYS_DLSEARCH_PATH
AM_INIT_AUTOMAKE([-Wall -Wno-override -Werror foreign])

AC_CONFIG_SRCDIR([pam_python.c])
AC_CONFIG_HEADERS([config.h])

# Checks for programs.
AC_PROG_CC
AC_PROG_INSTALL
AC_PROG_LN_S

# Checks for libraries.
AC_CHECK_LIB([pam], [pam_get_item], [],
  [AC_MSG_ERROR([PAM library not found])])

# Checks for header files.
AC_CHECK_HEADERS([dlfcn.h signal.h stdlib.h string.h syslog.h])
AC_CHECK_HEADERS([security/pam_modules.h], [],
  [AC_MSG_ERROR([PAM header files not found])])

# Checks for typedefs, structures, and compiler characteristics.
AC_TYPE_SIZE_T

# Checks for library functions.
AC_FUNC_MALLOC
AC_CHECK_FUNCS([strchr strdup strerror])

# Make host-platform details available
AC_CANONICAL_HOST
AC_DEFINE_UNQUOTED([CANONICAL_HOST], ["${host}"], [Canonical host])

# By default we bend the GNU rules to perform a typical PAModule install without
# requiring additional arguments to configure.  Compliance can be optionally restored
AC_ARG_ENABLE(gnu-compliance,
  AC_HELP_STRING([--enable-gnu-compliance],
                 [Install using GNU compliant paths instead of typical locations for PAModules]),
              [GNUCOMPLIANCE="enabled"],
              [GNUCOMPLIANCE="disabled"])

if test $GNUCOMPLIANCE = "disabled"; then
    # Put config files in FHS compliant location
    sysconfdir=/etc

    # Setup pam directory
    #  There is no agreement on where pam libs should live so search for one
    for dir in /lib/x86_64-linux-gnu/security /lib/i386-linux-gnu/security /lib/security /lib64/security; do
        if test -f $dir/pam_unix.so; then
            PAMDIR=$dir;
            break;
        fi
    done

    #  No luck with standard locations, setup a host-based default if possible
    if test -z $PAMDIR; then
        case "$host" in
            *darwin*)           PAMDIR='${libdir}/pam' ;;
            *x86_64-*-linux*)   PAMDIR='/lib64/security' ;;
            *linux*)            PAMDIR='/lib/security' ;;
            *)                  ;;
        esac
    fi
else
    PAMDIR=${libdir}/security
fi

# Setup toopher configuration directory
TOOPHER_CONF_DIR=${sysconfdir}/security/toopher
AC_SUBST(TOOPHER_CONF_DIR)

# Allow user to specify PAMDIR location with an argument
# (abuses AC_ARG_WITH like so many configure.ac scripts do)
AC_SUBST(PAMDIR)
AC_ARG_WITH(pam-dir,
  AC_HELP_STRING([--with-pam-dir=DIR],
                [Where to install PAModule]),
            [case "${withval}" in
            /*) PAMDIR="${withval}";;
            ./*|../*) AC_MSG_ERROR(Bad value for --with-pam-dir);;
            *)  PAMDIR="\$(exec_prefix)/lib/${withval}";;
            esac])
AC_MSG_NOTICE([PAM installation path $PAMDIR])

# Setup ADMINGROUP
AC_SUBST(ADMINGROUP, [toopher-admin])
AC_ARG_WITH(admin-group,
            AC_HELP_STRING([--with-admin-group=GROUP], [The UNIX group used to control read-access to the credentials-file. [default=toopher-admin, set to 'none' to disable]]),
  [ADMINGROUP=${withval}])

if test ${ADMINGROUP} != "none"; then
    AC_MSG_CHECKING([for existence of ${ADMINGROUP} group])
    if grep ^${ADMINGROUP}: /etc/group > /dev/null; then
        AC_MSG_RESULT([success])
    else
        AC_MSG_RESULT([fail])
        AC_MSG_ERROR([The configured admin group (${ADMINGROUP}) does not exist.  Create it, choose an existing group, or specify 'none' using --with-admin-group=GROUP])
    fi
fi

# Setup python
AX_PYTHON
if test -z $PYTHON_INCLUDE_DIR; then
  AC_MSG_ERROR([Missing python development header files])
fi
if test -z $PYTHON_LIB; then
  AC_MSG_ERROR([Missing python library])
fi
AX_PYTHON_PATH()
AX_PYTHON_VERSION_ENSURE([2.5])
AX_PYTHON_CSPEC
AX_PYTHON_LSPEC
AC_FOREACH([MODULE], toopher configobj argparse PyInstaller,
    AX_PYTHON_MODULE(MODULE, [fail]))

# Wrap-it up
AC_CONFIG_FILES([Makefile config.py])
AC_OUTPUT

AC_MSG_NOTICE([Summary of build options:

  Version:              ${VERSION}
  Host type:            ${host}
  Install prefix:       ${prefix}
  Compiler:             ${CC}
  PAM directory:        ${PAMDIR}
  Toopher config dir:   ${TOOPHER_CONF_DIR}
  Toopher admin group:  ${ADMINGROUP}
])	
