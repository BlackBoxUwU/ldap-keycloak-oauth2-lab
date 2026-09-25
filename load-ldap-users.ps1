# PowerShell script to load LDAP users on Windows
Write-Host "Verificando conexión con OpenLDAP..." -ForegroundColor Cyan

docker cp ldap/users.ldif openldap:/tmp/users.ldif
docker exec openldap ldapadd -c -x -H ldap://localhost:389 -D "cn=admin,dc=example,dc=com" -w adminpassword -f /tmp/users.ldif

Write-Host "Verificando usuarios alice y bob..." -ForegroundColor Cyan
$result = docker exec openldap ldapsearch -x -H ldap://localhost:389 -D "cn=admin,dc=example,dc=com" -w adminpassword -b "ou=users,dc=example,dc=com" "(uid=*)"

if ($result -match "uid: alice" -and $result -match "uid: bob") {
    Write-Host "✅ Usuarios LDAP cargados y verificados con éxito: alice, bob" -ForegroundColor Green
} else {
    Write-Host "⚠️ Advertencia: No se pudieron verificar los usuarios LDAP." -ForegroundColor Yellow
}
