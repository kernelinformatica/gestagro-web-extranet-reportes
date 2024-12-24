import paramiko
from flask import Flask, request, g,  jsonify, send_file, send_from_directory
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from decimal import Decimal
from conn.GestagroConnection import GestagroConnection as GestagroConnection
from datetime import datetime, timedelta
import logging
from flask import Flask
from flask_cors import CORS
from PIL import Image
app = Flask(__name__)
CORS(app)


@app.route('/reportes-pdf/<filename>')
def download_file(filename):
    return send_from_directory('/home/administrador/reportes-pdf', filename)


# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
#app.config['CORS_HEADERS'] = 'Content-Type'

#CORS(app)
# Configure logging
# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
# Initialize the database connection
parametros = {}

class GeneradorReportes(GestagroConnection):

    def __init__(self):
        print("-------------------------- INICIANDO PROCESO --------------------------------")
        super().__init__()
        self.datos = []
        self.datosUsu = []
        self.datosResuCer = []
        self.datosFichaCer = []
        self.maskCuenta = "0000000"
        self.maskNorComp = "0000-00000000"
        self.maskCosecha = "0000"
        print("Connection to MySQL ===================.")
        self.connGestagro = GestagroConnection()

    def upload_to_remote(self, local_path, remote_path, hostname, port, username, password):
        try:
            transport = paramiko.Transport((hostname, int(port)))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.put(local_path, remote_path)
            sftp.close()
            transport.close()
            print(f"Archivo {local_path} se ha enviado a gestagro satifactoriamente {remote_path} en el host  {hostname}")
        except Exception as e:
            print(f"Error al subir el archivo al host remoto: {e}")


    def generarReportes(self, file_path, parametros, titulo_reporte, reporte):
        print("generarReportes("+str(file_path)+")")
        hoy = datetime.today().date()
        logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',format='%(name)s - %(levelname)s - %(message)s')
        try:
            empresaPrefijo = parametros["coope"]
            cursor = self.connGestagro.conn.cursor()
            sql = "SELECT coope, coope_name AS nombre, coope_descri AS descripcion, mail, dominio,  cuit_cuil AS cuit, direccion, telefonos  FROM coope WHERE coope = "+str(empresaPrefijo)+""
            cursor.execute(sql)

        except Exception as e:
            logging.error(f"Error ejecutando query: {e}")
            print(f"Error ejecutando query: {e}")

        empresa = cursor.fetchone()
        prefijoEmpresa = empresa[0]
        nombreEmpresa = empresa[1]
        descripcionEmpresa = empresa[2]
        emailEmpresa = empresa[3]
        dominioEmpresa = empresa[4]
        cuitEmpresa = empresa[5]
        domicilioEmpresa = empresa[6]
        telefonosEmpresa = empresa[7]
        empresaSituacionIva = "Responsable Inscripto"
        cursor.close()
        data = []
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        page_number = 1
        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, dominioEmpresa, domicilioEmpresa, cuitEmpresa, empresaSituacionIva, telefonosEmpresa,hoy, parametros, page_number, reporte, titulo_reporte)
        # Reporte Stock General

        if reporte == 1:
            print(":: Generando Resumen de Cuenta Corriente ::")
            cursor = self.connGestagro.conn.cursor()
            cursor.execute("SELECT saldo FROM usuarios WHERE coope = " + str(prefijoEmpresa) + " AND cuenta = " + str(
                parametros["cuenta"]) + "")
            saldoCur = cursor.fetchone()
            total_saldo = saldoCur[0]

            #self.encabezadoReporteStockGeneral(c, height, parameters)
            # Paginación
            limit = 100  # Número de registros por página
            offset = 0
            more_data = True
            cursor = self.connGestagro.conn.cursor()
            cursor.execute("SELECT orden, vence, ingreso, detalle, concept, numero, numero_interno, debe, haber, saldo, resu_ctacte.idTipoComprobante, tiposcomprobantes.nombre AS tipoComprobanteNombre FROM resu_ctacte, tiposcomprobantes WHERE resu_ctacte.coope = "+str(prefijoEmpresa)+" AND resu_ctacte.cuenta = "+str(parametros["cuenta"])+" AND tiposcomprobantes.idTipoComprobante = resu_ctacte.idTipoComprobante ORDER BY orden asc")


            y = height - 170
            row_height = 15
            available_height = height - 200



            for row in cursor.fetchall():

                orden = row[0]
                vence = row[1]
                ingreso = row[2]
                detalle = row[3]
                concept = row[4]
                numero = row[5]
                numero_interno = row[6]
                debe = row[7]
                haber = row[8]
                saldo = row[9]
                idTipoComprobante = row[10]
                tipoComprobanteNombre = row[11]

                # Process each row as needed
                #print( f"Orden: {orden}, Vence: {vence}, Ingreso: {ingreso}, Detalle: {detalle}, Concept: {concept}, Numero: {numero}, Numero Interno: {numero_interno}, Debe: {debe}, Haber: {haber}, Saldo: {saldo}, ID Tipo Comprobante: {idTipoComprobante}, Tipo Comprobante Nombre: {tipoComprobanteNombre}")


                data.append({"orden": "" + str(orden), "vence": "" + str(vence) + "", "ingreso": "" + str(ingreso) + "",
                         "detalle": "" + str(detalle) + "", "concepto": "" + str(concept) + "",
                         "numero": "" + str(numero) + "", "numero_interno": "" + str(numero_interno) + "",
                         "debe": "" + str(debe) + "", "haber": "" + str(haber) + "", "saldo": "" + str(saldo) + "",
                         "id_tipo_comprobante": "" + str(idTipoComprobante) + "", "nombre_comprobante": "" + str(tipoComprobanteNombre)})

                # Table Data


            c.setFont("Helvetica", 8)

            for item in data:

                    if y < row_height:
                        page_number += 1
                        c.showPage()

                        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,dominioEmpresa, domicilioEmpresa, cuitEmpresa, empresaSituacionIva, telefonosEmpresa, hoy, parametros, page_number, reporte, titulo_reporte)
                        y = height - 170

                    c.drawRightString(30, y, item["orden"])
                    c.drawString(40, y, item["vence"])
                    c.drawString(90, y, item["ingreso"])
                    detalle = item["detalle"][:15]
                    c.drawString(140, y, detalle)
                    concepto = item["concepto"][:15]
                    c.drawString(220, y, concepto)
                    c.drawRightString(363, y, item["numero"])
                    nombreTipoComp = item['nombre_comprobante'][:15]

                    c.drawRightString(430, y, f"{Decimal(item['debe']):,.2f}")
                    c.drawRightString(500, y, f"{Decimal(item['haber']):,.2f}")
                    c.drawRightString(580, y, f"{Decimal(item['saldo']):,.2f}")
                    y -= row_height



            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(580, y, f"Saldo Vencido: {Decimal(total_saldo):,.2f}")
            y -= row_height
            c.setFont("Helvetica", 8)
            c.drawRightString(580, y, " (S.E.U.O)")

            y -= 10


        if reporte == 2:
            print(":: Generando Ficha de Cereales ::")
            cursor = self.connGestagro.conn.cursor()
            sql = "SELECT cereal, clase, cosecha, fecha, comprob_descri, comprob_nro, preimpreso,  kilos_en, kilos_sal , saldo  FROM ficha_cereal WHERE coope = "+str(prefijoEmpresa)+" and  cuenta = "+str(parametros["cuenta"])+" AND cereal = "+str(parametros["cereal"])+" AND cosecha = '"+str(parametros["cosecha"])+"' and clase = "+str(parametros["clase"])+" ORDER BY orden asc"
            print(sql)
            cursor.execute(sql)
            y = height - 170
            row_height = 15

            available_height = height - 200
            for row in cursor.fetchall():
                cereal = row[0]
                clase = row[1]
                cosecha=row[2]
                fecha = row[3]
                descripcion = row[4]
                nroComprobante = row[5]
                nroPreimpreso = row[6]
                kgEn = row[7]
                kgSal = row[8]
                saldo = row[9]
                data.append({"fecha": "" + str(fecha), "descripcion": "" + str(descripcion) + "", "nroComprobante": "" + str(nroComprobante) + "",
                             "nroPreimpreso": "" + str(nroPreimpreso) + "", "kgEn": "" + str(kgEn) + "", "kgSal": "" + str(kgSal) + "", "saldo": "" + str(saldo)})

            c.setFont("Helvetica", 8)
            for item in data:
                if y < row_height:
                    page_number += 1
                    c.showPage()
                    self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,
                                           dominioEmpresa, domicilioEmpresa, cuitEmpresa, empresaSituacionIva,
                                           telefonosEmpresa, hoy, parametros, page_number, reporte, titulo_reporte)
                    y = height - 170

                c.drawString(20, y, item["fecha"])
                c.drawString(100, y, item["descripcion"])
                c.drawRightString(250, y, item["nroComprobante"])
                c.drawRightString(350, y, f"{Decimal(item['kgEn']):,.2f}")
                c.drawRightString(450, y, f"{Decimal(item['kgSal']):,.2f}")
                c.drawRightString(580, y, f"{Decimal(item['saldo']):,.2f}")

                y -= row_height


            c.setFont("Helvetica", 8)
            c.drawRightString(580, y, " (S.E.U.O)")

            y -= 10



        if reporte == 3:
            print(":: Generando Resumen de Cuenta Corriente en Dólares::")
            cursor = self.connGestagro.conn.cursor()
            cursor.execute("SELECT saldoDolar FROM usuarios WHERE coope = " + str(prefijoEmpresa) + " AND cuenta = " + str(
                parametros["cuenta"]) + "")
            saldoCur = cursor.fetchone()
            total_saldo = saldoCur[0]

            #self.encabezadoReporteStockGeneral(c, height, parameters)
            # Paginación
            limit = 100  # Número de registros por página
            offset = 0
            more_data = True
            cursor = self.connGestagro.conn.cursor()
            cursor.execute("SELECT orden, vence, ingreso, detalle, concept, numero, numero_interno, debe, haber, saldo, resu_ctacte_uss.idTipoComprobante, tiposcomprobantes.nombre AS tipoComprobanteNombre FROM resu_ctacte_uss, tiposcomprobantes WHERE resu_ctacte_uss.coope = "+str(prefijoEmpresa)+" AND resu_ctacte_uss.cuenta = "+str(parametros["cuenta"])+" AND tiposcomprobantes.idTipoComprobante = resu_ctacte_uss.idTipoComprobante ORDER BY orden asc")


            y = height - 170
            row_height = 15
            available_height = height - 200



            for row in cursor.fetchall():

                orden = row[0]
                vence = row[1]
                ingreso = row[2]
                detalle = row[3]
                concept = row[4]
                numero = row[5]
                numero_interno = row[6]
                debe = row[7]
                haber = row[8]
                saldo = row[9]
                idTipoComprobante = row[10]
                tipoComprobanteNombre = row[11]

                # Process each row as needed
                #print( f"Orden: {orden}, Vence: {vence}, Ingreso: {ingreso}, Detalle: {detalle}, Concept: {concept}, Numero: {numero}, Numero Interno: {numero_interno}, Debe: {debe}, Haber: {haber}, Saldo: {saldo}, ID Tipo Comprobante: {idTipoComprobante}, Tipo Comprobante Nombre: {tipoComprobanteNombre}")


                data.append({"orden": "" + str(orden), "vence": "" + str(vence) + "", "ingreso": "" + str(ingreso) + "",
                         "detalle": "" + str(detalle) + "", "concepto": "" + str(concept) + "",
                         "numero": "" + str(numero) + "", "numero_interno": "" + str(numero_interno) + "",
                         "debe": "" + str(debe) + "", "haber": "" + str(haber) + "", "saldo": "" + str(saldo) + "",
                         "id_tipo_comprobante": "" + str(idTipoComprobante) + "", "nombre_comprobante": "" + str(tipoComprobanteNombre)})

                # Table Data


            c.setFont("Helvetica", 8)

            for item in data:

                    if y < row_height:
                        page_number += 1
                        c.showPage()

                        self.encabezadoReporte(c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa,dominioEmpresa, domicilioEmpresa, cuitEmpresa, empresaSituacionIva, telefonosEmpresa, hoy, parametros, page_number, reporte, titulo_reporte)
                        y = height - 170

                    c.drawRightString(30, y, item["orden"])
                    c.drawString(40, y, item["vence"])
                    c.drawString(90, y, item["ingreso"])
                    detalle = item["detalle"][:15]
                    c.drawString(140, y, detalle)
                    concepto = item["concepto"][:15]
                    c.drawString(220, y, concepto)
                    c.drawRightString(363, y, item["numero"])
                    nombreTipoComp = item['nombre_comprobante'][:15]

                    c.drawRightString(430, y, f"{Decimal(item['debe']):,.2f}")
                    c.drawRightString(500, y, f"{Decimal(item['haber']):,.2f}")
                    c.drawRightString(580, y, f"{Decimal(item['saldo']):,.2f}")
                    y -= row_height



            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(580, y, f"Saldo Vencido: {Decimal(total_saldo):,.2f}")
            y -= row_height
            c.setFont("Helvetica", 8)
            c.drawRightString(580, y, " (S.E.U.O)")

            y -= 10


        c.save()

        # Subo pdf a gestagro
        remote_path = f"/opt/domains/payaradomain/docroot/clientes/pdf/{file_path}"
        gen = GeneradorReportes()
        gen.connGestagro = GestagroConnection()
        hostname = gen.connGestagro.host
        port = gen.connGestagro.portSftp
        username = gen.connGestagro.userSftp
        password = gen.connGestagro.passwordSftp
        gen.upload_to_remote(file_path, remote_path, hostname, port, username, password)
        # cursor.close()

    # Example usage
    def encabezadoReporte(self, c, width, height, prefijoEmpresa, nombreEmpresa, descripcionEmpresa, dominioEmpresa, domicilioEmpresa, cuitEmpresa, empresaSituacionIva, telefonosEmpresa, hoy, parametros, page_number, reporte, titulo_reporte):

        cursor = self.connGestagro.conn.cursor()

        cursor.execute("select nombre, mail, saldo, fecha as fechaActualizacion from usuarios where coope = " + str(
            prefijoEmpresa) + " and cuenta = " + str(parametros["cuenta"]) + "")
        socioCur = cursor.fetchone()
        nombreSocio = socioCur[0]
        mailSocio = socioCur[1]
        saldoPesos = socioCur[2]
        fechaActualizacion = socioCur[3]
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - 30, height - 45, titulo_reporte[:40])
        c.setFont("Helvetica", 8)
        if reporte == 2:
            cursor = self.connGestagro.conn.cursor()
            sql = "SELECT cereal_descri, clase_descri FROM resu_cereal WHERE cereal_codigo = " + str(
                parametros["cereal"]) + " AND clase_codigo = " + str(parametros["clase"]) + " AND cosecha= '" + str(
                parametros["cosecha"]) + "' AND cuenta = " + str(parametros["cuenta"]) + ""
            cursor.execute(sql)
            row = cursor.fetchone()
            cerealNombre = row[0]
            claseDescripcion = row[1]
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(580, height - 60, str(cerealNombre) + " / " + str(claseDescripcion) + " / " + str(parametros["cosecha"]))

        c.setFont("Helvetica", 8)
        c.drawRightString(width - 30, height - 75, f"Página: {page_number}")

        # Title Left
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, height - 45, str(descripcionEmpresa))
        #c.setFont("Helvetica", 10)
        #c.drawString(100, height - 60, str(descripcionEmpresa))
        c.setFont("Helvetica", 8)
        c.drawString(100, height - 60, str(domicilioEmpresa))
        c.drawString(100, height - 70, "Cuit: " + str(cuitEmpresa) + ", " + str(empresaSituacionIva))

        # Logo
        logo_path = "img/" + str(prefijoEmpresa) + ".png"
        try:
            c.drawImage(logo_path, 15, height - 95, width=70, height=70)
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")

        c.setLineWidth(1)
        c.setStrokeColor(colors.grey)
        c.line(20, height - 90, 580, height - 90)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20, height - 105, str(nombreSocio))
        c.setFont("Helvetica", 8)
        c.drawString(20, height - 115, "Cuenta: " + str(parametros["cuenta"]))
        c.drawString(20, height - 125, "Email: " + str(mailSocio))

        c.drawRightString(width - 30, height - 105, "Emitido el: " + str(hoy))
        c.drawRightString(width - 30, height - 115, f"Info actualizada al: {fechaActualizacion}  (S.E.U.O)")
        c.line(20, height - 140, 580, height - 140)
        c.setFont("Helvetica-Bold", 8)


        if reporte == 1:
            c.drawString(44, height - 150, " - ")
            c.drawString(40, height - 150, "Vence")
            c.drawString(90, height - 150, "Ingreso")
            c.drawString(140, height - 150, "Detalle")
            c.drawString(220, height - 150, "Concepto")
            c.drawRightString(363, height - 150, "Nro")
            c.drawRightString(430, height - 150, "Debe")
            c.drawRightString(500, height - 150, "Haber")
            c.drawRightString(580, height - 150, "Saldo")
            c.line(20, height - 155, 580, height - 155)
        elif reporte == 2:
            c.drawString(20, height - 150, "Fecha")
            c.drawString(100, height - 150, "Descripción")
            c.drawRightString(250, height - 150, "Nro Comprobante")
            c.drawRightString(350, height - 150, "Ingresos")
            c.drawRightString(450, height - 150, "Salidas")
            c.drawRightString(580, height - 150, "Saldo")
            c.line(20, height - 155, 580, height - 155)
        # Adjust y coordinate after drawing the header
        c.setFont("Helvetica", 8)
        # Adjust y coordinate after drawing the header
        return height - 165






    def main(self, parameters,  titulo_reporte, reporteCodigo):

        self.generarReportes("reporte_" + str(reporteCodigo) + ".pdf", parameters, titulo_reporte, reporteCodigo)


@app.route('/dummy', methods=['GET'])
def dummy():
    import json

    data = {
        "code": "1",
        "version": "1.0",
        "status": 200,
        "description": "Generación de reportes en formato PDF.",
        "name": "Reportes PDF",
        "message": "Reportes PDF, esta activo y funciona correctamente.",
        "reports": ["Resumen de Cuenta Corriente", "Resumen de Cuenta Corriente en Dolares", "Ficha de Cereales"]
    }
    json_output = json.dumps(data, indent=4)
    print(json_output)
    return json_output



@app.before_request
def before_request_func():
    # Código que se ejecuta antes de procesar cada solicitud
    logging.debug("before_request_func called")

    print("Antes de procesar la solicitud....")
    #generar_reporte()





@app.route('/generarReportePdf', methods=['POST'])
def generar_reporte():
    print("Generando reporte... "+str(request.get_json()))
    logging.debug("generar_reporte called: "+str(request.get_json()))
    paramsJson = request.get_json()
    logging.error(f"Parametros query: {paramsJson}")
    tipo = paramsJson['tipo']
    cuenta = paramsJson['cuenta']
    coope = paramsJson['coope']

    parametros["tipo"] = tipo
    parametros["cuenta"] = cuenta
    parametros["coope"] = coope

    try:
        nombre = parametros["tipo"]
        reporte_codigo = 0
        titulo_reporte= "Reporte General"
        if parametros["tipo"] == "resumen-ctacte":
            titulo_reporte = "Resumen de Cuenta Corriente"
            reporte_codigo = 1
        elif parametros["tipo"] == "resumen-ctacte-uss":
            titulo_reporte = "Resumen De CtaCte en Dolares"
            reporte_codigo = 3
        elif parametros["tipo"] == "ficha-cereal":
            titulo_reporte = "Ficha de Cereales"
            reporte_codigo = 2
        else:
            titulo_reporte = "Resumen de Cuenta Corriente"
            reporte_codigo = 1

        file_path = f""+str(nombre)+"-"+str(parametros["cuenta"])+".pdf"
        generador = GeneradorReportes()
        generador.connGestagro = GestagroConnection()
        generador.generarReportes(file_path, parametros, titulo_reporte, reporte_codigo)




        print(":: GeneradorReportes culminó con éxito se envia el pdf para descargar ::")
        return send_file(file_path, as_attachment=True)
        print(":: PDF: " + file_path + " ::")
    except Exception as e:
        logging.error(f"Error generando el reporte: {e}")
        print(f"Error generando el reporte: {e}")
        return jsonify({"error": str(e)}), 500






if __name__ == "__main__":
   try:
       #generador = GeneradorReportes()
       parametros = {'tipo': "resumen-ctacte-uss", 'cuenta': "1100302", 'coope': "11"}
       """ parametros2 = {"coope": "11",
                     "cuenta": "1100302",
                     "cereal" : "23",
                     "clase": "0",
                     "cosecha" : "23/24"}"""
       #generador.main(parametros, "Resumen de cuenta en dolares", 3)
       app.run(debug=True, host='0.0.0.0', port=6003)

   except Exception as e:
        msg = f"A ocurrido un error al intentar iniciar el servicio GeneradorResportes: {e}"
        logging.error(f"Parametros query: {msg}")
        raise
