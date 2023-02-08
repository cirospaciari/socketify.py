
from dataclasses import dataclass

@dataclass
class AppListenOptions:
    port: int = 0
    host: str = None
    options: int = 0
    domain: str = None

    def __post_init__(self):
        if not isinstance(self.port, int):
            raise RuntimeError("port must be an int")
        if not isinstance(self.host, (type(None), str)):
            raise RuntimeError("host must be a str if specified")
        if not isinstance(self.domain, (type(None), str)):
            raise RuntimeError("domain must be a str if specified")
        if not isinstance(self.options, int):
            raise RuntimeError("options must be an int")
        if self.domain and (self.host or self.port != 0):
            raise RuntimeError(
                "if domain is specified, host and port will be no effect"
            )


@dataclass
class AppOptions:
    key_file_name: str = None
    cert_file_name: str = None
    passphrase: str = None
    dh_params_file_name: str = None
    ca_file_name: str = None
    ssl_ciphers: str = None
    ssl_prefer_low_memory_usage: int = 0

    def __post_init__(self):
        NoneType = type(None)

        if not isinstance(self.key_file_name, (NoneType, str)):
            raise RuntimeError("key_file_name must be a str if specified")
        if not isinstance(self.cert_file_name, (NoneType, str)):
            raise RuntimeError("cert_file_name must be a str if specified")
        if not isinstance(self.passphrase, (NoneType, str)):
            raise RuntimeError("passphrase must be a str if specified")
        if not isinstance(self.dh_params_file_name, (NoneType, str)):
            raise RuntimeError("dh_params_file_name must be a str if specified")
        if not isinstance(self.ca_file_name, (NoneType, str)):
            raise RuntimeError("ca_file_name must be a str if specified")
        if not isinstance(self.ssl_ciphers, (NoneType, str)):
            raise RuntimeError("ssl_ciphers must be a str if specified")
        if not isinstance(self.ssl_prefer_low_memory_usage, int):
            raise RuntimeError("ssl_prefer_low_memory_usage must be an int")
