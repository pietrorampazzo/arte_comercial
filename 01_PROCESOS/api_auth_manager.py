class APIClientWithAuth:
    """Wrapper para clientes de API com autenticação via headers ou parâmetros de querystring."""

    def __init__(self, client, auth_config: AuthConfig):
        self.client = client
        self.auth_config = auth_config

    def _get_auth_params(self) -> Dict[str, str]:
        """Retorna um dicionário com parâmetros de autenticação."""
        if self.auth_config.use_headers:
            return {f"Authorization": f"{self.auth_config.auth_type} {self.auth_config.auth_token}"}
        return {self.auth_config.auth_param_name: self.auth_config.auth_token}

    def _get_auth_headers(self) -> Dict[str, str]:
        """Retorna um dicionário com headers de autenticação."""
        if not self.auth_config.use_headers:
            return {}
        return {f"Authorization": f"{self.auth_config.auth_type} {self.auth_config.auth_token}"}

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Executa um GET na API com autenticação."""
        params = params or {}
        params.update(self._get_auth_params())
        response = self.client.get(url, params=params, headers=self._get_auth_headers())
        response.raise_for_status()
        return response.json()

    def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Executa um POST na API com autenticação."""
        data = data or {}
        data.update(self._get_auth_params())
        response = self.client.post(url, json=data, headers=self._get_auth_headers())
        response.raise_for_status()
        return response.json()


class AuthConfig:
    """Configurações de autenticação para a API."""

    def __init__(
        self,
        auth_token: str,
        auth_type: str = "Bearer",
        use_headers: bool = True,
        auth_param_name: str = "access_token",
    ):
        self.auth_token = auth_token
        self.auth_type = auth_type
        self.use_headers = use_headers
        self.auth_param_name = auth_param_name
