import sys
import platform


class Flags:
    FLAG_ANY = -1
    FLAG_TYPE_MASK = 0x00ff
    FLAG_LIBC4 = 0x0000
    FLAG_ELF = 0x0001
    FLAG_ELF_LIBC5 = 0x0002
    FLAG_ELF_LIBC6 = 0x0003
    FLAG_REQUIRED_MASK = 0xff00
    FLAG_SPARC_LIB64 = 0x0100
    FLAG_IA64_LIB64 = 0x0200
    FLAG_X8664_LIB64 = 0x0300
    FLAG_S390_LIB64 = 0x0400
    FLAG_POWERPC_LIB64 = 0x0500
    FLAG_MIPS64_LIBN32 = 0x0600
    FLAG_MIPS64_LIBN64 = 0x0700
    FLAG_X8664_LIBX32 = 0x0800
    FLAG_ARM_LIBHF = 0x0900
    FLAG_AARCH64_LIB64 = 0x0a00
    FLAG_ARM_LIBSF = 0x0b00
    FLAG_MIPS_LIB32_NAN2008 = 0x0c00
    FLAG_MIPS64_LIBN32_NAN2008 = 0x0d00
    FLAG_MIPS64_LIBN64_NAN2008 = 0x0e00
    FLAG_RISCV_FLOAT_ABI_SOFT = 0x0f00
    FLAG_RISCV_FLOAT_ABI_DOUBLE = 0x1000

    _type_descriptions = {
        FLAG_LIBC4: "libc4",
        FLAG_ELF: "ELF",
        FLAG_ELF_LIBC5: "libc5",
        FLAG_ELF_LIBC6: "libc6",
    }

    _required_descriptions = {
        FLAG_SPARC_LIB64: "64bit",
        FLAG_IA64_LIB64: "IA-64",
        FLAG_X8664_LIB64: "x86-64",
        FLAG_S390_LIB64: "64bit",
        FLAG_POWERPC_LIB64: "64bit",
        FLAG_MIPS64_LIBN32: "N32",
        FLAG_MIPS64_LIBN64: "64bit",
        FLAG_X8664_LIBX32: "x32",
        FLAG_ARM_LIBHF: "hard-float",
        FLAG_AARCH64_LIB64: "AArch64",
        FLAG_ARM_LIBSF: "soft-float",
        FLAG_MIPS_LIB32_NAN2008: "nan2008",
        FLAG_MIPS64_LIBN32_NAN2008: "N32,nan2008",
        FLAG_MIPS64_LIBN64_NAN2008: "64bit,nan2008",
        FLAG_RISCV_FLOAT_ABI_SOFT: "soft-float",
        FLAG_RISCV_FLOAT_ABI_DOUBLE: "double-float",
    }

    @classmethod
    def description(cls, value: int):
        return ",".join([
            cls._type_descriptions.get(value & cls.FLAG_TYPE_MASK, "unknown"),
            cls._required_descriptions.get(value & cls.FLAG_REQUIRED_MASK,
                                           str(value & cls.FLAG_REQUIRED_MASK))
        ])

    @classmethod
    def is_64bits(cls, value: int):
        return value & cls.FLAG_REQUIRED_MASK in {
            cls.FLAG_SPARC_LIB64,
            cls.FLAG_IA64_LIB64,
            cls.FLAG_X8664_LIB64,
            cls.FLAG_S390_LIB64,
            cls.FLAG_POWERPC_LIB64,
            cls.FLAG_MIPS64_LIBN64,
            cls.FLAG_AARCH64_LIB64,
            cls.FLAG_MIPS64_LIBN64_NAN2008,
        }

    @classmethod
    def expected_flags(cls, executable: str = sys.executable):
        """
        Returns a integer value representing the expected flag value from the
        cache, or None if not found
        """
        # Return a machine name, from the 'uname' system call
        machine = platform.machine()
        # Use the provided path to get a bit number
        bits, _ = platform.architecture(executable)

        # Reference of expected flags from (machine x bits)
        # Found in glibc:/sysdeps/unix/sysv/linux/<ARCH>/dl-cache.h
        matches = dict([
            (('x86_64', '64bit'), cls.FLAG_X8664_LIB64 | cls.FLAG_ELF_LIBC6),
            (('x86_64', '32bit'), cls.FLAG_X8664_LIBX32 | cls.FLAG_ELF_LIBC6),
            (('ppc64le', '64bit'),
             cls.FLAG_POWERPC_LIB64 | cls.FLAG_ELF_LIBC6),
            (('arm', '32bit'), cls.FLAG_ARM_LIBHF | cls.FLAG_ELF_LIBC6),
            (('aarch64', '64bit'),
             cls.FLAG_AARCH64_LIB64 | cls.FLAG_ELF_LIBC6),
            (('aarch64_be', '64bit'),
             cls.FLAG_AARCH64_LIB64 | cls.FLAG_ELF_LIBC6),
        ])

        return matches.get((machine, bits))
