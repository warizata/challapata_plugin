# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant, Qt, QDate
from qgis.PyQt.QtGui import QIcon, QFont, QColor
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QListWidgetItem
from qgis.PyQt.QtXml import QDomDocument
from qgis.utils import iface
from qgis.core import QgsProject, QgsFeature, QgsVectorLayer
from qgis.gui import QgsAttributeDialog, QgsMapToolIdentifyFeature
from PyQt5.QtCore import QDate, QRectF
from PyQt5.QtXml import QDomDocument

from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QLineEdit, QListWidget, 
    QPushButton, QLabel, QComboBox, QPlainTextEdit, QCheckBox
)
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
import os
import os.path
import processing
import requests
import json
import uuid
import traceback
from functools import partial
from datetime import date, datetime

# Importaciones locales agrupadas por funcionalidad
from .colegio_riberalta_dialog import (
    # Diálogos base
    ColegioRiberaltaDialog,
    
    # Exportación y manejo de titulares
    ExportDatabaseTitular,
    ListarTitular,
    ExportTitular,
    ExportTitularFeature,
    ExportDatabaseFeature,
    
    # Generación de informes y layouts
    GenerarLayout,
    GenerarInforme,
    GenerarInforme2,
    GenerarInforme3,
    
    # Selección de husos
    SeleccionarHuso,
    SeleccionarHusoLayout,
    SeleccionarHusoInforme,
    SeleccionarHusoInforme2,
    SeleccionarHusoInforme3,
    SeleccionarHusoFeature,
    SeleccionarHusoFeatureConstruccion,
    
    # Manejo de Features
    GuardarFeature,
    GuardarFeatureConstruccion,
    GuardarFeatureCambioTitular,
    GuardarFeatureUnion,
    GuardarFeatureDivide,
    GuardarLineaDivide,
    
    # Exportación de construcciones
    ExportDatabaseFeatureConstruccion,
    ExportPlantas,
    #ListarConstruccion,
    ListarConstruccionPlantas,
    ExportPlantas,
    
    # Exportación especializada
    ExportDatabaseEspecial,
    ExportDatabaseMejoras,
    ExportDatabasePlantas,
    
    # Selección de titulares
    SelectTitular,
    SelectTitularFeature,
    SelectTitularBuscaRef,
    SelectTitularBuscaNombre,
    SelectTitularFeatureBuscaRef,
    SelectTitularFeatureBuscaNombre,
    
    # Manejo de construcciones y terrenos
    SelectConstruccionPlantaBuscaRef,
    SelectTerrenoLayoutBuscaRef,
    SelectTerrenoLayoutBuscaNombre,
    SelectTerrenoInformeBuscaRef,
    SelectTerrenoInformeBuscaNombre,
    SelectTerrenoInforme2BuscaRef,
    SelectTerrenoInforme2BuscaNombre,
    SelectTerrenoInforme3BuscaRef,
    SelectTerrenoInforme3BuscaNombre,
    
    # Cambio de titular
    SelecTitularCambioTitular,
    SelectTitularCambioTitularBuscaRef,
    SelectTitularCambioTitularBuscaNombre,
    ConfirmarGuardarTitular,
    
    # Unión de features
    SelecTitularUnion,
    SelectTitularUnionBuscaRef,
    SelectTitularUnionBuscaNombre,
    ConfirmarUnion,
    
    # Información de unión
    InfoFormaUnion,
    InfoInclinacionUnion,
    InfoMaterialCalzadaUnion,
    InfoTipoCalzadaUnion,
    InfoUbicacionUnion,
    InfoCodigoUnion,
    InfoZonaUnion,
    
    # División de features
    SelecTitularDivide1,
    SelecTitularDivide2,
    SelectTitularDivide1BuscaRef,
    SelectTitularDivide2BuscaRef,
    SelectTitularDivide1BuscaNombre,
    SelectTitularDivide2BuscaNombre,
    ConfirmarDivide,
    InfoCodigoDivide1,
    InfoCodigoDivide2
)

from .catastro import (
    CatastroWidget,
    EjesVialesWidget,
    ZonasWidget,
    ManzanasDialog, 
    OrdenesTrabajo
)

from qgis.core import (
    QgsDataSourceUri,
    QgsFillSymbol,
    QgsSymbol,
    QgsSimpleFillSymbolLayer,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsVectorLayerSimpleLabeling,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsPointXY,
    QgsGeometry,
    QgsRasterLayer,
    QgsPrintLayout,
    QgsLayoutItemPage,
    QgsReadWriteContext,
    QgsMapSettings,
    QgsRectangle,
    QgsLayoutSize,
    QgsUnitTypes,
    QgsLayoutExporter,
    QgsLayoutItemTextTable,
    QgsLayoutTableColumn,
    QgsLayoutFrame,
    QgsLayoutPoint,
    QgsTextBufferSettings,
    QgsLabeling,
    QgsLayoutItemMap,
    QgsLayoutItemPage,
    QgsPrintLayout,
    QgsLayoutExporter,
    QgsReadWriteContext,
    QgsProject,
    QgsVectorLayer,
    QgsLayoutItemLabel,
    QgsFeature
)
from .export_database import ExportDialog
from .DriverDataBase import DataBaseDriver
from .resources import *

class MiPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.export_dialog = None
        self.identify_tool = None

    def initGui(self):
        # Aquí va tu código existente de initGui
        # Agrega un botón o acción para activar la selección
        self.action = QAction("Seleccionar Terreno", self.iface.mainWindow())
        self.action.triggered.connect(self.activar_seleccion)
        self.iface.addToolBarIcon(self.action)

    def activar_seleccion(self):
        """Activa la herramienta de selección en el mapa"""
        # Obtener la capa de terrenos
        layer = QgsProject.instance().mapLayersByName('terrenos19')[0]
        
        # Crear y configurar la herramienta de identificación
        self.identify_tool = QgsMapToolIdentifyFeature(self.canvas)
        self.identify_tool.setLayer(layer)
        
        # Conectar la señal de identificación
        self.identify_tool.featureIdentified.connect(self.on_feature_identified)
        
        # Activar la herramienta
        self.canvas.setMapTool(self.identify_tool)

    def on_feature_identified(self, feature):
        """Maneja el evento cuando se selecciona un polígono"""
        try:
            # Crear y mostrar el diálogo de exportación
            self.export_dialog = ExportDialog()
            self.export_dialog.cargar_poligono(feature)
            self.export_dialog.show()
            
            # Opcional: Desactivar la herramienta de selección después de seleccionar
            self.canvas.unsetMapTool(self.identify_tool)
            
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error al cargar el polígono: {str(e)}")

    def unload(self):
        # Aquí va tu código existente de unload
        if self.action:
            self.iface.removeToolBarIcon(self.action)      


class TerrenosManager:
    def __init__(self, db_driver):
        """
        Inicializa el gestor de terrenos con el driver de base de datos
        """
        self.db = db_driver
        self.id_terreno_seleccionado = None
        #self.setup_search()  # Agregar esta línea

    def setup_search(self):
        """Configurar el buscador y la lista"""
        try:
            # Asegurarnos que searchBox está conectado al método de filtrado
            if hasattr(self, 'searchBox'):
                self.searchBox.clear()  # Limpiar cualquier texto existente
                self.searchBox.textChanged.connect(self.filter_list)
                print("Buscador conectado a filter_list")
            else:
                print("Error: No se encontró searchBox")

            # Verificar que la lista existe
            if hasattr(self, 'list_bbdd'):
                print(f"Lista encontrada con {self.list_bbdd.count()} elementos")
            else:
                print("Error: No se encontró list_bbdd")

        except Exception as e:
            print(f"Error en setup_search: {str(e)}")

    def populate_list(self):
        """Poblar la lista con códigos desde la base de datos"""
        try:
            if hasattr(self, 'list_bbdd'):
                self.list_bbdd.clear()
                # Consulta SQL para obtener los códigos
                sql = """
                SELECT codigo 
                FROM catastro.terrenos19 
                ORDER BY codigo
                """
                resultados = self.db.read(sql)
                
                # Agregar códigos a la lista
                for row in resultados:
                    self.list_bbdd.addItem(str(row[0]))
                
                print(f"Lista poblada con {self.list_bbdd.count()} códigos")
            else:
                print("Error: No se encontró list_bbdd")
                
        except Exception as e:
            print(f"Error poblando lista: {str(e)}")

    def filter_list(self, text):
        """Filtrar la lista basado en el texto de búsqueda"""
        try:
            if not hasattr(self, 'list_bbdd'):
                print("Error: No se encontró list_bbdd")
                return

            search_text = text.lower().strip()
            print(f"Filtrando por: '{search_text}'")

            # Mostrar todos los items si no hay texto de búsqueda
            if not search_text:
                for i in range(self.list_bbdd.count()):
                    self.list_bbdd.item(i).setHidden(False)
                return

            # Filtrar items
            items_encontrados = 0
            for i in range(self.list_bbdd.count()):
                item = self.list_bbdd.item(i)
                if item:
                    matches = search_text in item.text().lower()
                    item.setHidden(not matches)
                    if matches:
                        items_encontrados += 1

            print(f"Se encontraron {items_encontrados} coincidencias")

        except Exception as e:
            print(f"Error en filter_list: {str(e)}")
    
    def validar_codigo(self, codigo):
        """
        Valida el formato del código de terreno
        """
        pattern = r'^\d+\.\d+\.\d+\.\d+\.\d+$'
        if not re.match(pattern, codigo):
            raise ValueError("El código debe tener el formato: X.X.X.X.X")
        return True

    def verificar_duplicado(self, codigo, id_actual=None):
        """
        Verifica si existe un terreno con el mismo código
        """
        sql = """
        SELECT id, codigo, direccion 
        FROM catastro.terrenos19 
        WHERE codigo = %s AND id != COALESCE(%s, -1)
        """
        return self.db.read(sql, params=(codigo, id_actual), multi=False)

    def seleccionar_poligono(self, feature):
        """
        Selecciona un polígono verificando su validez
        """
        try:
            layer = iface.activeLayer()
            
            if layer is None or layer.name() != 'terrenos19':
                self.db.showMessage("Por favor, seleccione la capa terrenos19", 2, 3)
                return False
                
            if not feature.isValid():
                self.db.showMessage("El polígono seleccionado no es válido", 2, 3)
                return False
                
            self.id_terreno_seleccionado = feature.attribute('id')
            codigo = feature.attribute('codigo')
            
            if not self.id_terreno_seleccionado:
                self.db.showMessage("El polígono no tiene un ID válido", 2, 3)
                return False

            try:
                self.validar_codigo(codigo)
            except ValueError as e:
                self.db.showMessage(str(e), 2, 3)
                return False

            duplicado = self.verificar_duplicado(codigo, self.id_terreno_seleccionado)
            if duplicado:
                self.db.showMessage(f"Advertencia: Existe otro terreno con el código {codigo}", 2, 3)
                
            self.cargar_datos_poligono()
            return True
            
        except Exception as ex:
            self.db.showMessage(f"Error al seleccionar el polígono: {str(ex)}", 2, 3)
            self.id_terreno_seleccionado = None
            return False

    def cargar_datos_poligono(self):
        """
        Carga los datos del polígono seleccionado en los controles
        """
        try:
            sql = """
            SELECT *
            FROM catastro.terrenos19 
            WHERE id = %s
            """
            datos = self.db.read(sql, params=(self.id_terreno_seleccionado,), multi=False)
            
            if datos:
                # Cargar datos en los controles
                self.txt_calle.setPlainText(str(datos.get('direccion', '')))
                self.txt_manzano.setPlainText(str(datos.get('manzano', '')))
                self.txt_predio.setPlainText(str(datos.get('predio', '')))
                self.txt_sub.setPlainText(str(datos.get('subpredio', '')))
                self.txt_zona.setPlainText(str(datos.get('zona', '')))
                self.txt_suptest.setPlainText(str(datos.get('suptest', '')))
                self.txt_base.setPlainText(str(datos.get('base', '')))
                self.txt_frente.setPlainText(str(datos.get('frente', '')))
                self.txt_fondo.setPlainText(str(datos.get('fondo', '')))
                
                # Establecer los índices de los combobox
                self.comboBox_ubicacion.setCurrentIndex(datos.get('ubicacion', 0) or 0)
                self.comboBox_inclinacion.setCurrentIndex(datos.get('topografia', 0) or 0)
                self.comboBox_forma.setCurrentIndex(datos.get('forma', 0) or 0)
                self.comboBox_calzada.setCurrentIndex(datos.get('material_via', 0) or 0)
                self.comboBox_tipocalzada.setCurrentIndex(datos.get('via', 0) or 0)
                
                # Establecer los checkboxes
                self.checkBox_agua.setChecked(datos.get('agua', False))
                self.checkBox_alcantarilla.setChecked(datos.get('alcantarillado', False))
                self.checkBox_energia.setChecked(datos.get('energia', False))
                self.checkBox_telefono.setChecked(datos.get('telefono', False))
                self.checkBox_internet.setChecked(datos.get('internet', False))
                self.checkBox_transporte.setChecked(datos.get('transporte', False))
                
        except Exception as ex:
            self.db.showMessage(f"Error al cargar datos: {str(ex)}", 2, 3)

    def verificar_permisos(self):
        """Verifica los permisos de la base de datos"""
        try:
            # Verificar permisos
            sql_permisos = """
            SELECT grantee, privilege_type 
            FROM information_schema.role_table_grants 
            WHERE table_name = 'terrenos19' 
            AND table_schema = 'catastro';
            """
            permisos = self.db.read(sql_permisos)
            print("Permisos actuales:", permisos)
            return True
        except Exception as ex:
            print(f"Error verificando permisos: {str(ex)}")
            return False

    def actualizar_terreno(self):
        """
        Método actualizado para coincidir con la estructura exacta de la tabla terrenos19
        """
        if not self.id_terreno_seleccionado:
            self.db.showMessage("Seleccione un polígono", 2, 3)
            return

        try:
            self.db.begin()

            # Construir el diccionario de campos a actualizar
            campos_update = {}
            
            # Campos de texto (character varying)
            campos_update['codigo'] = self.txt_referencia.text().strip()
            if not campos_update['codigo']:
                raise Exception("El código es obligatorio")
                
            campos_update['direccion'] = self.txt_calle.text().strip() or None
            campos_update['manzano'] = self.txt_manzano.text().strip() or None
            campos_update['predio'] = self.txt_predio.text().strip() or None
            campos_update['subpredio'] = self.txt_sub.text().strip() or None
            campos_update['base'] = self.txt_base.text().strip() or None
            
            # Campos numéricos
            try:
                campos_update['zona'] = int(self.txt_zona.text().strip()) if self.txt_zona.text().strip() else None
                campos_update['suptest'] = float(self.txt_suptest.text().strip()) if self.txt_suptest.text().strip() else None
                campos_update['frente'] = float(self.txt_frente.text().strip()) if self.txt_frente.text().strip() else None
                campos_update['fondo'] = float(self.txt_fondo.text().strip()) if self.txt_fondo.text().strip() else None
            except ValueError as e:
                raise Exception(f"Error en conversión de números: {str(e)}")
                
            # Campos de ComboBox (integer)
            campos_update['ubicacion'] = self.comboBox_ubicacion.currentIndex() if self.comboBox_ubicacion.currentIndex() >= 0 else None
            campos_update['topografia'] = self.comboBox_inclinacion.currentIndex() if self.comboBox_inclinacion.currentIndex() >= 0 else None
            campos_update['forma'] = self.comboBox_forma.currentIndex() if self.comboBox_forma.currentIndex() >= 0 else None
            campos_update['material_via'] = self.comboBox_calzada.currentIndex() if self.comboBox_calzada.currentIndex() >= 0 else None
            campos_update['via'] = self.comboBox_tipocalzada.currentIndex() if self.comboBox_tipocalzada.currentIndex() >= 0 else None
            
            # Campos boolean
            campos_update['agua'] = self.checkBox_agua.isChecked()
            campos_update['alcantarillado'] = self.checkBox_alcantarilla.isChecked()
            campos_update['energia'] = self.checkBox_energia.isChecked()
            campos_update['telefono'] = self.checkBox_telefono.isChecked()
            campos_update['internet'] = self.checkBox_internet.isChecked()
            campos_update['transporte'] = self.checkBox_transporte.isChecked()

            # Construir la consulta SQL dinámicamente
            campos = []
            valores = []
            params = []
            
            for campo, valor in campos_update.items():
                campos.append(f"{campo} = %s")
                params.append(valor)
                valores.append(f"{campo}: {valor} ({type(valor)})")

            # Agregar el ID al final de los parámetros
            params.append(self.id_terreno_seleccionado)
            
            # Construir la consulta SQL
            update_sql = f"""
            UPDATE catastro.terrenos19 
            SET {', '.join(campos)}
            WHERE id = %s
            RETURNING *;
            """

            # Debug - Imprimir información
            print("\nValores a actualizar:")
            for valor in valores:
                print(valor)
                
            print("\nConsulta SQL:")
            print(update_sql)
            
            print("\nParámetros:")
            for i, param in enumerate(params):
                print(f"Param {i}: {param} ({type(param)})")

            # Ejecutar la actualización
            result = self.db.update(update_sql, params=params)
            if not result:
                raise Exception("No se pudo actualizar el registro")

            # Confirmar la transacción
            self.db.commit()
            self.db.showMessage("Actualización exitosa", 3, 3)

            # Verificar la actualización
            verify_sql = "SELECT * FROM catastro.terrenos19 WHERE id = %s;"
            result_after = self.db.read(verify_sql, params=[self.id_terreno_seleccionado])
            print("\nRegistro actualizado:", result_after)

        except Exception as ex:
            self.db.rollback()
            self.db.showMessage(f"Error: {str(ex)}", 2, 3)
            print(f"Error completo: {str(ex)}")
            import traceback
            print("Traceback completo:")
            print(traceback.format_exc())
       
            
       
       

    def insertar_terreno(self, feature, titular_id):
        """
        Inserta un nuevo terreno con todas las validaciones
        """
        try:
            self.db.begin()
            
            nuevo_codigo = self.txt_referencia.toPlainText()
            self.validar_codigo(nuevo_codigo)

            duplicado = self.verificar_duplicado(nuevo_codigo)
            if duplicado:
                raise Exception(f"Ya existe un terreno con el código {nuevo_codigo}")

            geom = feature.geometry()
            if not geom.isGeosValid():
                raise Exception("La geometría del terreno no es válida")

            insert_sql = """
            INSERT INTO catastro.terrenos19 (
                codigo, direccion, superficie, zona, via, agua, 
                alcantarillado, energia, telefono, transporte, internet, 
                titular, topografia, forma, ubicacion, frente, fondo, 
                suptest, manzano, predio, subpredio, base,
                material_via, geom
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                ST_Multi(ST_Force2D(ST_Transform(ST_GeomFromText(%s, %s), 32719)))
            )
            """
            
            params = [
                nuevo_codigo,
                self.txt_calle.toPlainText() or None,
                geom.area(),
                safe_int(self.txt_zona.toPlainText()),
                self.comboBox_tipocalzada.currentIndex(),
                self.checkBox_agua.isChecked(),
                self.checkBox_alcantarilla.isChecked(),
                self.checkBox_energia.isChecked(),
                self.checkBox_telefono.isChecked(),
                self.checkBox_transporte.isChecked(),
                self.checkBox_internet.isChecked(),
                titular_id,
                self.comboBox_inclinacion.currentIndex(),
                self.comboBox_forma.currentIndex(),
                self.comboBox_ubicacion.currentIndex(),
                safe_float(self.txt_frente.toPlainText()),
                safe_float(self.txt_fondo.toPlainText()),
                safe_float(self.txt_suptest.toPlainText()),
                self.txt_manzano.toPlainText() or None,
                self.txt_predio.toPlainText() or None,
                self.txt_sub.toPlainText() or None,
                self.txt_base.toPlainText() or None,
                self.comboBox_calzada.currentIndex(),
                geom.asWkt(),
                feature.crs().authid()[5:]
            ]
            
            self.db.create(insert_sql, params=params)
            self.db.commit()
            self.db.showMessage("Terreno registrado exitosamente", 3, 3)
            
        except Exception as ex:
            self.db.rollback()
            self.db.showMessage(f"Error: {str(ex)}", 2, 3)

class DialogoConstruccion(QDialog):
    def __init__(self, iface, parent=None, construccion_id=None):
        """Constructor de la clase DialogoConstruccion."""
        super(DialogoConstruccion, self).__init__(parent)
        
        # Cargar la interfaz desde el archivo .ui
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'export_database_feature_construccion.ui'), self)
        
        self.iface = iface
        self.construccion_id = construccion_id
        self.setupDb()
        self.inicializar_combos()
        self.conectar_eventos()
        
        # Cargar datos existentes inmediatamente
        self.cargar_construcciones_existentes()
        
        # Si se proporciona un ID de construcción, cargarlo automáticamente
        if construccion_id:
            self.cargar_construccion_por_id(construccion_id)
            self.setWindowTitle(f"Gestión de Construcción - ID: {construccion_id}")

    def inicializar_combos(self):
        """Inicializa los combos con valores predeterminados."""
        # Configurar ComboBox de conservación
        conservacion_items = ["Seleccione...", "Bueno", "Regular", "Malo", "Ruina"]
        self.comboBox_conservacion.clear()
        self.comboBox_conservacion.addItems(conservacion_items)
        
        # Configurar ComboBox de uso
        uso_items = ["Seleccione...", "Residencial", "Comercial", "Industrial", "Servicios", "Otro"]
        self.comboBox_uso.clear()
        self.comboBox_uso.addItems(uso_items)
        
        # Configurar ComboBox de tipo
        tipo_items = ["Seleccione...", "Casa", "Edificio", "Galpón", "Local", "Otro"]
        self.comboBox_tipo.clear()
        self.comboBox_tipo.addItems(tipo_items)
        
        # Configurar ComboBox de revestimiento
        revestimiento_items = ["Seleccione...", "Ladrillo", "Hormigón", "Madera", "Metal", "Otro"]
        self.comboBox_revestimiento.clear()
        self.comboBox_revestimiento.addItems(revestimiento_items)

    def cargar_construccion_por_id(self, id_construccion):
        """Cargar una construcción específica por su ID."""
        try:
            print(f"Cargando construcción con ID: {id_construccion}")
            query = f"""
                SELECT * FROM catastro.construcciones19 
                WHERE id = {id_construccion}
            """
            resultado = self.db.read(sql=query, multi=False)
            
            if resultado:
                self.mostrar_datos_construccion(resultado)
                
                # Calcular número de plantas basado en el código y numbloque
                self.calcular_y_actualizar_num_plantas(id_construccion)
                
                # Identificar planta baja automáticamente
                self.identificar_planta_baja_y_ordenar(id_construccion)
                
                # Destacar visualmente el item de la lista correspondiente
                self.destacar_item_en_lista(id_construccion)
            else:
                print(f"No se encontró la construcción con ID: {id_construccion}")
                QMessageBox.warning(self, "Advertencia", f"No se encontró la construcción con ID: {id_construccion}")
                
        except Exception as e:
            print(f"Error al cargar construcción por ID: {str(e)}")
            import traceback
            traceback.print_exc()

    def setupDb(self):
        """Configurar la conexión a la base de datos."""
        try:
            # Aquí asumimos que tienes una clase Driver similar a tu código original
            # Si tienes otro mecanismo de conexión, adáptalo según sea necesario
            from .DriverDataBase import DataBaseDriver
            self.db = DataBaseDriver()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar con la base de datos: {str(e)}")
            self.close()

    def conectar_eventos(self):
        """Conectar los eventos de la interfaz."""
        # Conectar botones principales
        if hasattr(self, 'btn_exportdb'):
            self.btn_exportdb.clicked.connect(self.actualizar_construccion)
        elif hasattr(self, 'btn_guardar'):
            self.btn_guardar.clicked.connect(self.actualizar_construccion)
            
        if hasattr(self, 'btn_cerrar'):
            self.btn_cerrar.clicked.connect(self.close)
            
        # Conectar búsqueda
        if hasattr(self, 'pushButton'):
            self.pushButton.clicked.connect(self.buscar_construccion)
            
        if hasattr(self, 'searchBox') and hasattr(self, 'list_bbdd'):
            self.searchBox.textChanged.connect(self.filtrar_lista)
            self.list_bbdd.itemClicked.connect(self.cargar_datos_construccion)

    def cargar_construcciones_existentes(self):
        """Cargar la lista de construcciones existentes."""
        try:
            query = """
                SELECT id, codigo, numbloque
                FROM catastro.construcciones19 
                ORDER BY id
            """
            resultados = self.db.read(sql=query, multi=True)
            
            if hasattr(self, 'list_bbdd'):
                self.list_bbdd.clear()
                for construccion in resultados:
                    item_text = f"ID: {construccion['id']} - Código: {construccion['codigo']} - Bloque: {construccion['numbloque']}"
                    self.list_bbdd.addItem(item_text)
                
        except Exception as e:
            print(f"Error al cargar construcciones: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error al cargar construcciones: {str(e)}")

    def filtrar_lista(self, texto):
        """Filtrar la lista según el texto de búsqueda."""
        if hasattr(self, 'list_bbdd'):
            for i in range(self.list_bbdd.count()):
                item = self.list_bbdd.item(i)
                item.setHidden(texto.lower() not in item.text().lower())

    def destacar_item_en_lista(self, id_construccion):
        """Destaca el item correspondiente al ID de construcción en la lista."""
        if hasattr(self, 'list_bbdd'):
            for i in range(self.list_bbdd.count()):
                item = self.list_bbdd.item(i)
                if f"ID: {id_construccion}" in item.text():
                    self.list_bbdd.setCurrentItem(item)
                    break

    def buscar_construccion(self):
        """Buscar una construcción específica."""
        if not hasattr(self, 'searchBox'):
            return
            
        texto_busqueda = self.searchBox.text().strip()
        if not texto_busqueda:
            QMessageBox.warning(self, "Advertencia", "Ingrese un código o ID para buscar")
            return

        try:
            # Intentar interpretar como ID si es numérico
            is_id = texto_busqueda.isdigit()
            
            if is_id:
                query = f"""
                    SELECT * FROM catastro.construcciones19 
                    WHERE id = {texto_busqueda}
                """
            else:
                query = f"""
                    SELECT * FROM catastro.construcciones19 
                    WHERE codigo LIKE '%{texto_busqueda}%'
                """
                
            resultado = self.db.read(sql=query, multi=True)
            
            if resultado and len(resultado) > 0:
                self.mostrar_datos_construccion(resultado[0])
                
                # Si encontramos la construcción, guardamos su ID
                self.construccion_id = resultado[0].get('id')
                
                # Calcular y actualizar plantas
                self.calcular_y_actualizar_num_plantas(self.construccion_id)
                
                # Identificar planta baja
                self.identificar_planta_baja_y_ordenar(self.construccion_id)
                
                # Destacar en la lista
                self.destacar_item_en_lista(self.construccion_id)
            else:
                QMessageBox.information(self, "Información", "No se encontró la construcción")
                
        except Exception as e:
            print(f"Error en la búsqueda: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error en la búsqueda: {str(e)}")

    def mostrar_datos_construccion(self, datos):
        """Mostrar los datos de la construcción en el formulario."""
        try:
            # Verificar que los widgets necesarios existen
            if not all(hasattr(self, attr) for attr in ['cod', 'anyo', 'plantas', 'dormitorios', 'banyos']):
                print("Faltan widgets necesarios en el formulario")
                return
                
            # Datos básicos - adaptamos para manejar tanto dict como objetos
            self.cod.setPlainText(str(datos.get('id') if isinstance(datos, dict) else getattr(datos, 'id', '')))
            self.anyo.setPlainText(str(datos.get('anyo') if isinstance(datos, dict) else getattr(datos, 'anyo', '')))
            self.plantas.setPlainText(str(datos.get('plantas') if isinstance(datos, dict) else getattr(datos, 'plantas', '')))
            self.dormitorios.setPlainText(str(datos.get('dormitorios') if isinstance(datos, dict) else getattr(datos, 'dormitorios', '')))
            self.banyos.setPlainText(str(datos.get('banyos') if isinstance(datos, dict) else getattr(datos, 'banyos', '')))
            
            # Comboboxes - convertimos índices a textos según corresponda
            conservacion_idx = int(datos.get('estadoconservacion', 0) if isinstance(datos, dict) else getattr(datos, 'estadoconservacion', 0))
            uso_idx = int(datos.get('uso', 0) if isinstance(datos, dict) else getattr(datos, 'uso', 0))
            tipo_idx = int(datos.get('tipoconstruccion', 0) if isinstance(datos, dict) else getattr(datos, 'tipoconstruccion', 0))
            revestimiento_idx = int(datos.get('revestimiento', 0) if isinstance(datos, dict) else getattr(datos, 'revestimiento', 0))
            
            # Asegurar que los índices estén dentro del rango válido
            self.comboBox_conservacion.setCurrentIndex(min(conservacion_idx, self.comboBox_conservacion.count()-1))
            self.comboBox_uso.setCurrentIndex(min(uso_idx, self.comboBox_uso.count()-1))
            self.comboBox_tipo.setCurrentIndex(min(tipo_idx, self.comboBox_tipo.count()-1))
            self.comboBox_revestimiento.setCurrentIndex(min(revestimiento_idx, self.comboBox_revestimiento.count()-1))
            
            # Checkboxes para características
            self.checkBox_ascensor.setChecked(bool(datos.get('ascensores', False) if isinstance(datos, dict) else getattr(datos, 'ascensores', False)))
            self.checkBox_calefaccion.setChecked(bool(datos.get('calefaccion', False) if isinstance(datos, dict) else getattr(datos, 'calefaccion', False)))
            self.checkBox_aire.setChecked(bool(datos.get('aire', False) if isinstance(datos, dict) else getattr(datos, 'aire', False)))
            self.checkBox_sanitarios.setChecked(bool(datos.get('sanitarios', False) if isinstance(datos, dict) else getattr(datos, 'sanitarios', False)))
            self.checkBox_escalera.setChecked(bool(datos.get('escalera', False) if isinstance(datos, dict) else getattr(datos, 'escalera', False)))
            self.checkBox_lavandera.setChecked(bool(datos.get('lavanderia', False) if isinstance(datos, dict) else getattr(datos, 'lavanderia', False)))
            self.checkBox_agua.setChecked(bool(datos.get('tanque', False) if isinstance(datos, dict) else getattr(datos, 'tanque', False)))
            self.checkBox_area.setChecked(bool(datos.get('servicio', False) if isinstance(datos, dict) else getattr(datos, 'servicio', False)))
            
        except Exception as e:
            print(f"Error al mostrar datos: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error al mostrar datos: {str(e)}")

    def recopilar_datos_formulario(self):
        """Recopilar los datos actuales del formulario."""
        try:
            return {
                'id': self.cod.toPlainText().strip(),
                'anyo': self.anyo.toPlainText().strip(),
                'plantas': self.plantas.toPlainText().strip(),
                'dormitorios': self.dormitorios.toPlainText().strip(),
                'banyos': self.banyos.toPlainText().strip(),
                'estadoconservacion': self.comboBox_conservacion.currentIndex(),
                'uso': self.comboBox_uso.currentIndex(),
                'tipoconstruccion': self.comboBox_tipo.currentIndex(),
                'revestimiento': self.comboBox_revestimiento.currentIndex(),
                'ascensores': self.checkBox_ascensor.isChecked(),
                'calefaccion': self.checkBox_calefaccion.isChecked(),
                'aire': self.checkBox_aire.isChecked(),
                'sanitarios': self.checkBox_sanitarios.isChecked(),
                'escalera': self.checkBox_escalera.isChecked(),
                'lavanderia': self.checkBox_lavandera.isChecked(),
                'tanque': self.checkBox_agua.isChecked(),
                'servicio': self.checkBox_area.isChecked()
            }
        except Exception as e:
            print(f"Error al recopilar datos: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error al recopilar datos: {str(e)}")
            return {}

    def validar_datos(self, datos):
        """Validar los datos antes de guardar."""
        if not datos.get('id'):
            QMessageBox.warning(self, "Validación", "El ID de construcción es obligatorio")
            return False
            
        campos_numericos = ['anyo', 'plantas', 'dormitorios', 'banyos']
        for campo in campos_numericos:
            if datos.get(campo) and not datos.get(campo).isdigit():
                QMessageBox.warning(self, "Validación", f"El campo {campo} debe ser numérico")
                return False
                
        return True

    def actualizar_construccion(self):
        """Actualizar o crear una nueva construcción."""
        datos = self.recopilar_datos_formulario()
        
        if not self.validar_datos(datos):
            return
            
        try:
            id_construccion = datos['id']
            
            # Verificar si la construcción existe
            query_check = f"""
                SELECT id FROM catastro.construcciones19 
                WHERE id = {id_construccion}
            """
            existe = self.db.read(sql=query_check, multi=False)
            
            if existe:
                # Actualizar construcción existente
                query = f"""
                    UPDATE catastro.construcciones19 SET
                        anyo = '{datos['anyo']}',
                        plantas = {datos['plantas']},
                        dormitorios = {datos['dormitorios']},
                        banyos = {datos['banyos']},
                        estadoconservacion = {datos['estadoconservacion']},
                        uso = {datos['uso']},
                        tipoconstruccion = {datos['tipoconstruccion']},
                        revestimiento = {datos['revestimiento']},
                        ascensores = {datos['ascensores']},
                        calefaccion = {datos['calefaccion']},
                        aire = {datos['aire']},
                        sanitarios = {datos['sanitarios']},
                        escalera = {datos['escalera']},
                        lavanderia = {datos['lavanderia']},
                        tanque = {datos['tanque']},
                        servicio = {datos['servicio']}
                    WHERE id = {id_construccion}
                """
                self.db.create(sql=query)
                mensaje = "Construcción actualizada correctamente"
            else:
                # No deberíamos llegar aquí ya que estamos editando una construcción existente
                QMessageBox.warning(self, "Advertencia", "No se encontró la construcción para actualizar")
                return
            
            QMessageBox.information(self, "Éxito", mensaje)
            
            # Actualizar plantas si ha cambiado el número
            self.actualizar_plantas_si_cambio(id_construccion, int(datos['plantas']))
            
            # Recargar la lista de construcciones
            self.cargar_construcciones_existentes()
            
            # Destacar la construcción actualizada
            self.destacar_item_en_lista(id_construccion)
            
        except Exception as e:
            print(f"Error al guardar los datos: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al guardar los datos: {str(e)}")

    def cargar_datos_construccion(self, item):
        """Cargar datos cuando se selecciona una construcción de la lista."""
        try:
            # Extraer el ID de construcción del texto del item
            texto_item = item.text()
            if "ID:" not in texto_item:
                return
                
            id_construccion = texto_item.split('-')[0].replace('ID:', '').strip()
            
            # Consulta para obtener los datos principales
            query = f"""
                SELECT * FROM catastro.construcciones19 
                WHERE id = {id_construccion}
            """
            resultado = self.db.read(sql=query, multi=False)
            
            if resultado:
                # Almacenar el ID actual
                self.construccion_id = id_construccion
                
                # Mostrar datos en el formulario
                self.mostrar_datos_construccion(resultado)
                
                # Calcular y actualizar plantas
                self.calcular_y_actualizar_num_plantas(id_construccion)
                
                # Identificar planta baja
                self.identificar_planta_baja_y_ordenar(id_construccion)
            
        except Exception as e:
            print(f"Error al cargar los datos: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error al cargar los datos: {str(e)}")
    
    def calcular_y_actualizar_num_plantas(self, id_construccion):
        """
        Calcula el número real de plantas basado en las construcciones_plantas19
        y actualiza el campo en el formulario.
        """
        try:
            # Primero, obtener el código y bloque de esta construcción
            query_info = f"""
                SELECT codigo, numbloque 
                FROM catastro.construcciones19 
                WHERE id = {id_construccion}
            """
            info = self.db.read(sql=query_info, multi=False)
            
            if not info:
                print(f"No se encontró información para la construcción ID: {id_construccion}")
                return
                
            codigo = info.get('codigo')
            bloque = info.get('numbloque')
            
            # Contar cuántas plantas existen en construcciones_plantas19
            query_count = f"""
                SELECT COUNT(*) as num_plantas
                FROM catastro.construcciones_plantas19
                WHERE id_construccion = {id_construccion}
            """
            resultado = self.db.read(sql=query_count, multi=False)
            
            plantas_registradas = 0
            if resultado and 'num_plantas' in resultado:
                plantas_registradas = resultado['num_plantas']
            
            # Contar también cuántas construcciones existen con este código y bloque (enfoque alternativo)
            query_count_alt = f"""
                SELECT COUNT(*) as num_plantas
                FROM catastro.construcciones19
                WHERE codigo = '{codigo}' AND numbloque = {bloque}
            """
            resultado_alt = self.db.read(sql=query_count_alt, multi=False)
            
            plantas_calculadas = 0
            if resultado_alt and 'num_plantas' in resultado_alt:
                plantas_calculadas = resultado_alt['num_plantas']
            
            # Determinar el número de plantas final (tomamos el máximo)
            num_plantas_final = max(plantas_registradas, plantas_calculadas)
            
            if num_plantas_final > 0:
                # Actualizar el campo en la interfaz
                if hasattr(self, 'plantas'):
                    current_value = self.plantas.toPlainText().strip()
                    if current_value != str(num_plantas_final):
                        self.plantas.setPlainText(str(num_plantas_final))
                        print(f"Número de plantas actualizado automáticamente a {num_plantas_final}")
                    
                    # Si hay discrepancia, mostrar un mensaje
                    if plantas_registradas != plantas_calculadas and plantas_registradas > 0 and plantas_calculadas > 0:
                        QMessageBox.information(
                            self, 
                            "Información", 
                            f"Nota: Se han encontrado {plantas_calculadas} construcciones con el mismo código y bloque, " +
                            f"pero hay {plantas_registradas} plantas registradas en la tabla de plantas. " +
                            f"Se ha usado el valor máximo ({num_plantas_final})."
                        )
                
                # Actualizar también en la base de datos
                update_query = f"""
                    UPDATE catastro.construcciones19
                    SET plantas = {num_plantas_final}
                    WHERE id = {id_construccion}
                """
                self.db.create(sql=update_query)
                print(f"Base de datos actualizada con {num_plantas_final} plantas para ID {id_construccion}")
                
        except Exception as e:
            print(f"Error al calcular el número de plantas: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def identificar_planta_baja_y_ordenar(self, id_construccion):
        """
        Identifica la planta baja entre las plantas registradas y asegura 
        que las plantas estén correctamente ordenadas (0, 1, 2, etc.)
        """
        try:
            # Obtener todas las plantas de esta construcción
            query_plantas = f"""
                SELECT id, id_planta, anyo, superficie
                FROM catastro.construcciones_plantas19
                WHERE id_construccion = {id_construccion}
                ORDER BY id_planta
            """
            plantas = self.db.read(sql=query_plantas, multi=True)
            
            if not plantas:
                print(f"No se encontraron plantas para la construcción ID: {id_construccion}")
                return
                
            # Verificar si existe la planta baja (id_planta = 0)
            tiene_planta_baja = False
            for planta in plantas:
                if planta.get('id_planta') == 0:
                    tiene_planta_baja = True
                    break
            
            # Si no hay planta baja, designar la primera planta como planta baja
            if not tiene_planta_baja and plantas:
                # Obtener el ID de la primera planta
                primera_planta_id = plantas[0].get('id')
                
                # Actualizar esta planta para que sea la planta baja
                update_query = f"""
                    UPDATE catastro.construcciones_plantas19
                    SET id_planta = 0
                    WHERE id = {primera_planta_id}
                """
                self.db.create(sql=update_query)
                print(f"Se ha designado la planta con ID {primera_planta_id} como planta baja")
                
                # Reordenar las demás plantas
                self.reordenar_plantas_consecutivas(id_construccion)
                
                # Mostrar mensaje
                QMessageBox.information(
                    self, 
                    "Información", 
                    "Se ha identificado automáticamente la planta baja y reordenado las plantas."
                )
            
        except Exception as e:
            print(f"Error al identificar planta baja: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def reordenar_plantas_consecutivas(self, id_construccion):
        """
        Asegura que las plantas estén numeradas consecutivamente (0, 1, 2, etc.)
        """
        try:
            # Obtener todas las plantas actuales ordenadas por id_planta
            query_plantas = f"""
                SELECT id, id_planta
                FROM catastro.construcciones_plantas19
                WHERE id_construccion = {id_construccion}
                ORDER BY id_planta
            """
            plantas = self.db.read(sql=query_plantas, multi=True)
            
            if not plantas:
                return
                
            # Verificar si las plantas están ordenadas correctamente
            esperado = 0
            for planta in plantas:
                planta_actual = planta.get('id_planta')
                
                # Si hay un salto en la numeración, corregirlo
                if planta_actual != esperado:
                    update_query = f"""
                        UPDATE catastro.construcciones_plantas19
                        SET id_planta = {esperado}
                        WHERE id = {planta.get('id')}
                    """
                    self.db.create(sql=update_query)
                    print(f"Planta con ID {planta.get('id')} reordenada de {planta_actual} a {esperado}")
                
                esperado += 1
                
        except Exception as e:
            print(f"Error al reordenar plantas: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def actualizar_plantas_si_cambio(self, id_construccion, nuevo_num_plantas):
        """
        Actualiza las plantas si el número ha cambiado.
        
        Args:
            id_construccion (int): ID de la construcción.
            nuevo_num_plantas (int): Nuevo número de plantas.
        """
        try:
            # Obtener el número actual de plantas registradas
            query_count = f"""
                SELECT COUNT(*) as num_plantas
                FROM catastro.construcciones_plantas19
                WHERE id_construccion = {id_construccion}
            """
            resultado = self.db.read(sql=query_count, multi=False)
            
            if resultado and 'num_plantas' in resultado:
                plantas_actuales = resultado['num_plantas']
                
                # Si el número ha aumentado, crear las plantas adicionales
                if nuevo_num_plantas > plantas_actuales:
                    # Obtener datos de la construcción para las nuevas plantas
                    query_construccion = f"""
                        SELECT anyo, superficie, geom
                        FROM catastro.construcciones19
                        WHERE id = {id_construccion}
                    """
                    datos_construccion = self.db.read(sql=query_construccion, multi=False)
                    
                    if datos_construccion:
                        anyo = datos_construccion.get('anyo', '0')
                        superficie = datos_construccion.get('superficie', 0)
                        
                        # Crear plantas nuevas (empezando desde el número actual)
                        for i in range(plantas_actuales, nuevo_num_plantas):
                            # Obtener el siguiente ID disponible
                            sql_ultimo_id = "SELECT COALESCE(MAX(id), 0) + 1 AS proximo_id FROM catastro.construcciones_plantas19"
                            resultado_id = self.db.read(sql=sql_ultimo_id, multi=False)
                            proximo_id = resultado_id.get('proximo_id', 1)
                            
                            # Determinar el id_planta (número de planta)
                            # Si i=0 y no hay planta baja, crear planta baja
                            # Si no, asignar id_planta correlativo
                            if i == 0:
                                # Verificar si ya existe planta baja
                                check_planta_baja = f"""
                                    SELECT id FROM catastro.construcciones_plantas19
                                    WHERE id_construccion = {id_construccion} AND id_planta = 0
                                """
                                tiene_planta_baja = self.db.read(sql=check_planta_baja, multi=False)
                                
                                if tiene_planta_baja:
                                    continue  # Ya existe la planta baja
                                
                                id_planta = 0  # Planta baja
                            else:
                                id_planta = i
                            
                            # Insertar la nueva planta
                            insert_query = f"""
                                INSERT INTO catastro.construcciones_plantas19 
                                (id, id_construccion, id_planta, anyo, superficie, geom)
                                SELECT 
                                    {proximo_id},
                                    {id_construccion}, 
                                    {id_planta}, 
                                    '{anyo}', 
                                    {superficie}, 
                                    geom
                                FROM catastro.construcciones19
                                WHERE id = {id_construccion}
                            """
                            self.db.create(sql=insert_query)
                            print(f"Planta {id_planta} creada para construcción ID: {id_construccion}")
                        
                        # Mensaje informativo
                        plantas_creadas = nuevo_num_plantas - plantas_actuales
                        if plantas_creadas > 0:
                            QMessageBox.information(
                                self, 
                                "Información", 
                                f"Se han creado {plantas_creadas} nuevas plantas automáticamente."
                            )
                
                # Si el número ha disminuido, eliminar plantas sobrantes
                elif nuevo_num_plantas < plantas_actuales:
                    # Confirmar con el usuario
                    respuesta = QMessageBox.question(
                        self,
                        "Confirmación",
                        f"El número de plantas ha disminuido de {plantas_actuales} a {nuevo_num_plantas}. " +
                        f"¿Desea eliminar las plantas sobrantes?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if respuesta == QMessageBox.Yes:
                        # Obtener las plantas ordenadas por id_planta (ascendente)
                        query_plantas = f"""
                            SELECT id, id_planta
                            FROM catastro.construcciones_plantas19
                            WHERE id_construccion = {id_construccion}
                            ORDER BY id_planta
                        """
                        plantas = self.db.read(sql=query_plantas, multi=True)
                        
                        # Eliminar plantas por encima del nuevo límite
                        # Conservamos la planta baja (id_planta=0) y tantas plantas como especificado
                        plantas_a_conservar = nuevo_num_plantas
                        plantas_eliminadas = 0
                        
                        for i, planta in enumerate(plantas):
                            # Si es la planta baja, la conservamos
                            if planta.get('id_planta') == 0:
                                continue
                                
                            # Si ya hemos conservado suficientes plantas, eliminamos
                            if i >= plantas_a_conservar:
                                delete_query = f"""
                                    DELETE FROM catastro.construcciones_plantas19
                                    WHERE id = {planta.get('id')}
                                """
                                self.db.create(sql=delete_query)
                                plantas_eliminadas += 1
                        
                        if plantas_eliminadas > 0:
                            QMessageBox.information(
                                self, 
                                "Información", 
                                f"Se han eliminado {plantas_eliminadas} plantas sobrantes."
                            )
                
        except Exception as e:
            print(f"Error al actualizar plantas: {str(e)}")
            import traceback
            traceback.print_exc()


    
class ColegioRiberalta:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):

        self.ortofoto  = r'D:\PROYECTO CHALLAPATA\ZONIFICACION_2024\ortofoto\ortofotoChalla.ecw' #! PATH ORTOFOTO
        
        # Save reference to the QGIS interface
        self.iface = iface
        
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # Declare instance attributes
        self.actions = []
        self.menu = 'Colegio Riberalta'

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.driver = DataBaseDriver()
        
        
         # Inicializar los diálogos
        try:
            self.dlg_export_titular = ExportTitular()
            self.dlg_export_feature_construccion = ExportDatabaseFeatureConstruccion()
            self.dlg_export_plantas = ExportPlantas()  # Cambiado de ExportDatabasePlantas
            self.dlg_listar_construccion_plantas = ListarConstruccionPlantas()
            print("Diálogos inicializados correctamente")
        except Exception as e:
            print(f"Error al inicializar diálogos: {str(e)}")
        
        # Cargar el archivo UI usando la ruta correcta con 'UI' en mayúsculas
        ui_file = os.path.join(self.plugin_dir, 'UI', 'listar_construccion_plantas.ui')
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self.dlg_listar_construccion_plantas)
        else:
            print(f"No se encontró el archivo UI en: {ui_file}")
        
        # Conectar las señales
        self.setup_ui_connections()
        
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu('&Colegio Riberalta',action)
            self.iface.removeToolBarIcon(action)

   
    def add_action(self, icon_path, text, callback, add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
     
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        
        
        action.triggered.connect(callback)
        action.setEnabled(True)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action
        
    def guardar_co_titular(self):
        """
        Función para guardar un co-titular asociado a un titular principal
        """
        try:
            # Verificar si los campos del co-titular están completos
            valor_nombre = self.dlg_export_titular.txt_nombre_2.text().strip()
            valor_apellidos = self.dlg_export_titular.txt_apellidos_2.text().strip()
            valor_documento = self.dlg_export_titular.txt_documento_2.text().strip()
            
            if not valor_apellidos or not valor_nombre or not valor_documento:
                self.driver.showMessage('Por favor complete todos los campos del co-titular', 1, 5)
                return False
            
            # Primero mostrar el diálogo para seleccionar un titular
            self.dlg_select_titular.show()
            
            # Cargar la lista de titulares
            self.cargar_titular()
            
            # Desconectar cualquier conexión previa para evitar duplicados
            try:
                self.dlg_select_titular.btn_select_titular.clicked.disconnect()
            except:
                pass
            
            # Conectar el botón de selección con una función que continuará el proceso
            self.dlg_select_titular.btn_select_titular.clicked.connect(
                lambda: self.finalizar_guardar_co_titular(valor_nombre, valor_apellidos, valor_documento)
            )
            
            return True
            
        except Exception as e:
            self.driver.showMessage(f'Error al iniciar guardado de co-titular: {str(e)}', 2, 5)
            print(f"ERROR DETALLADO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def finalizar_guardar_co_titular(self, nombre, apellidos, documento):
        try:
            print("[DEBUG] Iniciando finalizar_guardar_co_titular")
            
            # Obtener el titular seleccionado
            list_widget = self.dlg_select_titular.list_titular
            current = list_widget.currentItem()
            
            if not current:
                self.driver.showMessage('Seleccione un titular', 1, 5)
                print("[DEBUG] No hay titular seleccionado")
                return
                
            # Obtener el ID del titular
            titular_text = current.text()
            print(f"[DEBUG] Texto del titular: {titular_text}")
            
            titular_parts = titular_text.split()
            print(f"[DEBUG] Partes del texto: {titular_parts}")
            
            if not titular_parts:
                self.driver.showMessage('Error al obtener el ID del titular', 1, 5)
                print("[DEBUG] No se pudieron obtener partes del texto")
                return
                
            titular_id = titular_parts[0]
            print(f"[DEBUG] ID del titular: {titular_id}")
            
            # Verificar si el titular existe en titular_old (tabla con la restricción)
            sql_check_old = f"SELECT id FROM catastro.titular_old WHERE id = {titular_id}"
            print(f"[DEBUG] SQL para verificar en titular_old: {sql_check_old}")
            
            exists_in_old = self.driver.read(sql_check_old, multi=False)
            print(f"[DEBUG] Resultado de verificación en titular_old: {exists_in_old}")
            
            # Si no existe en titular_old pero existe en titular, copiarlo
            if not exists_in_old:
                print("[DEBUG] El titular no existe en titular_old, verificando en titular")
                
                sql_check_new = f"SELECT * FROM catastro.titular WHERE id = {titular_id}"
                print(f"[DEBUG] SQL para verificar en titular: {sql_check_new}")
                
                exists_in_new = self.driver.read(sql_check_new, multi=False)
                print(f"[DEBUG] Resultado de verificación en titular: {exists_in_new}")
                
                if exists_in_new:
                    print("[DEBUG] El titular existe en titular, copiándolo a titular_old")
                    
                    # Preparar valores y manejar posibles valores nulos
                    nombre_titular = exists_in_new.get('nombre', '')
                    if nombre_titular is None:
                        nombre_titular = ''
                    
                    apellidos_titular = exists_in_new.get('apellidos', '')
                    if apellidos_titular is None:
                        apellidos_titular = ''
                    
                    documento_titular = exists_in_new.get('documento', '')
                    if documento_titular is None:
                        documento_titular = ''
                    
                    tipo_doc = exists_in_new.get('tipo_doc', 0)
                    if tipo_doc is None:
                        tipo_doc = 0
                    
                    caracter = exists_in_new.get('caracter', 0)
                    if caracter is None:
                        caracter = 0
                    
                    documento_prop = exists_in_new.get('documento_prop', 0)
                    if documento_prop is None:
                        documento_prop = 0
                    
                    adquisicion = exists_in_new.get('adquisicion', 0)
                    if adquisicion is None:
                        adquisicion = 0
                    
                    # Escapar comillas simples
                    nombre_titular = nombre_titular.replace("'", "''")
                    apellidos_titular = apellidos_titular.replace("'", "''")
                    documento_titular = documento_titular.replace("'", "''")
                    
                    # Construir la consulta SQL para copiar el titular
                    sql_copy = f"""
                    INSERT INTO catastro.titular_old 
                    (id, nombre, apellidos, documento, tipo_doc, caracter, documento_prop, adquisicion)
                    VALUES 
                    ({titular_id}, 
                    '{nombre_titular}', 
                    '{apellidos_titular}', 
                    '{documento_titular}', 
                    {tipo_doc}, 
                    {caracter}, 
                    {documento_prop}, 
                    {adquisicion})
                    """
                    
                    print(f"[DEBUG] SQL para copiar titular: {sql_copy}")
                    
                    copy_result = self.driver.create(sql_copy, msg=False)
                    print(f"[DEBUG] Resultado de copiar titular: {copy_result}")
                    
                    if not copy_result:
                        self.driver.showMessage('No se pudo sincronizar el titular', 2, 5)
                        print("[DEBUG] Error al copiar el titular")
                        return
                else:
                    self.driver.showMessage('El titular no existe en ninguna tabla', 2, 5)
                    print("[DEBUG] El titular no existe en ninguna tabla")
                    return
            
            # Ahora que estamos seguros de que el titular existe en titular_old,
            # procedemos a guardar el co-titular
            nombre = nombre.replace("'", "''")
            apellidos = apellidos.replace("'", "''")
            documento = documento.replace("'", "''")
            
            # Verificar si ya existe un co-titular con este documento para este titular
            sql_check_existing = f"""
            SELECT id FROM catastro.co_titular 
            WHERE documento = '{documento}' AND titular_id = {titular_id}
            """
            
            print(f"[DEBUG] SQL para verificar co-titular existente: {sql_check_existing}")
            
            existing_cotitular = self.driver.read(sql_check_existing, multi=False)
            print(f"[DEBUG] Resultado de verificación de co-titular existente: {existing_cotitular}")
            
            if existing_cotitular:
                self.driver.showMessage('Ya existe un co-titular con ese documento para este titular', 2, 5)
                print("[DEBUG] Co-titular ya existe")
                return
            
            # Construir la consulta SQL para insertar el co-titular
            sql = f"""
            INSERT INTO catastro.co_titular 
            (titular_id, nombre, apellidos, documento)
            VALUES
            ({titular_id}, '{nombre}', '{apellidos}', '{documento}')
            """
            
            print(f"[DEBUG] SQL para insertar co-titular: {sql}")
            
            insert_result = self.driver.create(sql)
            print(f"[DEBUG] Resultado de insertar co-titular: {insert_result}")
            
            if insert_result:
                self.dlg_export_titular.txt_apellidos_2.clear()
                self.dlg_export_titular.txt_nombre_2.clear()
                self.dlg_export_titular.txt_documento_2.clear()
                self.dlg_select_titular.close()
                
                self.driver.showMessage('Co-titular guardado exitosamente', 3, 3)
                print("[DEBUG] Co-titular guardado exitosamente")
            else:
                self.driver.showMessage('Error al guardar el co-titular', 2, 5)
                print("[DEBUG] Error al guardar el co-titular")
            
        except Exception as ex:
            self.driver.showMessage(f'Error: {str(ex)}', 1, 15)
            print(f"[DEBUG] ERROR DETALLADO: {str(ex)}")
            import traceback
            traceback.print_exc()

    def actualizar_co_titular(self):
        # Similar a guardar_co_titular pero con UPDATE
        pass

    def cancelar_co_titular(self):
        self.dlg_export_titular.txt_apellidos_2.clear()
        self.dlg_export_titular.txt_nombre_2.clear()
        self.dlg_export_titular.txt_documento_2.clear()
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Inicializar todos los diálogos
        self.dlg = ColegioRiberaltaDialog()
        self.dlg_export_titular = ExportDatabaseTitular()
        self.dlg_export_feature_construccion = ExportDatabaseFeatureConstruccion()
        self.dlg_listar_construccion_plantas = ListarConstruccionPlantas(parent=self.iface.mainWindow(), db_driver=self.driver)  # Agregar esta línea

        # Conectar los botones del diálogo de titular
        self.dlg_export_titular.btn_guardar_co.clicked.connect(self.guardar_co_titular)
        self.dlg_export_titular.btn_update_co.clicked.connect(self.actualizar_co_titular)
        self.dlg_export_titular.btn_cancelar_co.clicked.connect(self.cancelar_co_titular)
        
        # Conectar los botones del diálogo de construcción plantas
        self.dlg_listar_construccion_plantas.btn_agregar_planta.clicked.connect(self.abrir_formulario_plantas)
        self.dlg_listar_construccion_plantas.btn_const_selec_ref.clicked.connect(self.planta_busca_ref)
        self.dlg_listar_construccion_plantas.btn_const_limpiar.clicked.connect(self.limpiar_busqueda_plantas)       
        
        
        
        icon_path = self.plugin_dir + "/icon/search.png"
        self.add_action(
            icon_path,
            text='Buscar Lotes',
            callback=self.abrir_busqueda,
            parent=self.iface.mainWindow())
        
        icon_path = self.plugin_dir + "/icon/search.png"
        self.add_action(
        icon_path,
            text='Buscar Lotes',
        callback=self.abrir_ordenesTrabajo,
        parent=self.iface.mainWindow())

        
        icon_path = self.plugin_dir + "/icon/user.jpg"
        self.add_action(
            icon_path,
            text= 'Carga Datos Titular',
            callback=self.abrir_dialogo_titular,
            parent=self.iface.mainWindow())

        icon_path = self.plugin_dir + "/icon/folder.png"
        self.add_action(
            icon_path,
            text= 'Carga Archivo en BBDD',
            callback=self.abrir_dialogo_cargacsv,
            parent=self.iface.mainWindow())
            
            
        icon_path = self.plugin_dir + "/icon/map.png"
        self.add_action(
            icon_path,
            text= 'Carga Parcela desde Interfaz',
            callback=self.abrir_dialogo_guardarfeature, 
            parent=self.iface.mainWindow())
            
            
        icon_path = self.plugin_dir + "/icon/house.png"
        self.add_action(
            icon_path,
            text= 'Carga Construcción desde Interfaz',
            callback=self.abrir_dialogo_guardarfeature_construccion,
            parent=self.iface.mainWindow())
            
        icon_path = self.plugin_dir + "/icon/cement.png"
        self.add_action(
            icon_path,
            text= 'Carga Materiales de Construcción',
            callback=self.abrir_dialogo_listarconstruccion_plantas,
            parent=self.iface.mainWindow())
            
            
        icon_path = self.plugin_dir + "/icon/layout.png"
        self.add_action(
            icon_path,
            text= 'Generar Plano',
            callback=self.abrir_dialogo_layout,
            parent=self.iface.mainWindow())
            
            
        icon_path = self.plugin_dir + "/icon/report.png"
        self.add_action(
            icon_path,
            text= 'Generar Informe',
            callback=self.abrir_dialogo_informe,
            parent=self.iface.mainWindow())
            
            
        icon_path = self.plugin_dir + "/icon/report2.png"
        self.add_action(
            icon_path,
            text= 'Generar Certificado Catastral',
            callback=self.abrir_dialogo_informe2,
            parent=self.iface.mainWindow())
            
            
        icon_path = self.plugin_dir + "/icon/report3.png"
        self.add_action(
            icon_path,
            text= 'Generar Certificado de Avalúo',
            callback=self.abrir_dialogo_informe3,
            parent=self.iface.mainWindow())
            



        icon_path = self.plugin_dir + "/icon/usersicon.png"
        self.add_action(
            icon_path,
            text= 'Cambiar Titular de Terreno',
            callback=self.abrir_dialogo_guardarfeature_cambiarTitular,
            parent=self.iface.mainWindow())
            


        icon_path = self.plugin_dir + "/icon/uniricon.png"
        self.add_action(
            icon_path,
            text= 'Unir dos Terrenos',
            callback=self.abrir_guardar_feature_union,
            parent=self.iface.mainWindow())
            
            
            
            
        icon_path = self.plugin_dir + "/icon/dividiricon.png"
        self.add_action(
            icon_path,
            text= 'Separar Terreno',
            callback=self.abrir_guardar_feature_divide,
            parent=self.iface.mainWindow())

        icon_path = self.plugin_dir + "/icon/manzana.png"
        self.add_action(icon_path,
            text= 'Manzanos',
            callback=self.abrir_dialogo_guardarManzanas,
            parent=self.iface.mainWindow())

        icon_path = self.plugin_dir + "/icon/road.png"
        self.add_action(icon_path,
            text= 'Eje de Vias',
            callback=self.abrir_dialog_guardar_ejevias,
            parent=self.iface.mainWindow())
        
        icon_path = self.plugin_dir + "/icon/zona.png"
        self.add_action(icon_path,
            text= 'Zonificacion',
            callback=self.abrir_dialogo_guardar_zonas,
            parent=self.iface.mainWindow())

                       
        self.dlg_export_feature_construccion = ExportDatabaseFeatureConstruccion()
    
        # Desconectar señales previas si existen
        try:
            self.dlg_export_feature_construccion.pushButton.clicked.disconnect()
        except:
            pass
        
        # Conectar la señal
        self.dlg_export_feature_construccion.pushButton.clicked.connect(self.referenciar_construccion)
        
        
        
        ######################################################################VARIABLES CARGADAS DE DIALOG##########################################
        

        # will be set False in run()
        self.first_start = True

        self.dlg_busqueda = CatastroWidget()
        self.dlg_ot = OrdenesTrabajo()
        self.dlg_ejes_viales = EjesVialesWidget()
        
        self.dlg = ColegioRiberaltaDialog()
        
        self.dlg_listar_titular = ListarTitular()
        self.dlg_export_titular_feature = ExportTitularFeature()
        
        self.dlg_export = ExportDialog()
        self.dlg_export_feature = ExportDatabaseFeature()
        
        self.dlg_layout = GenerarLayout()
        self.dlg_informe = GenerarInforme()
        self.dlg_huso = SeleccionarHuso()
        self.dlg_huso_layout = SeleccionarHusoLayout()
        self.dlg_huso_informe = SeleccionarHusoInforme()
        self.dlg_guardar_feature = GuardarFeature()

        self.dlg_guardar_ejevia = GuardarFeature() #! EjeVias
        self.dlg_guardar_manzanas = ManzanasDialog() #! Manzanos
        self.dlg_guardar_zona = ZonasWidget() #! Zonas

        self.dlg_huso_feature = SeleccionarHusoFeature()
        self.dlg_guardar_feature_construccion = GuardarFeatureConstruccion()
        self.dlg_huso_feature_construccion = SeleccionarHusoFeatureConstruccion()
        self.dlg_export_plantas = ExportPlantas()
        self.dlg_huso_informe2 = SeleccionarHusoInforme2()
        self.dlg_huso_informe3 = SeleccionarHusoInforme3()
        self.dlg_informe2 = GenerarInforme2()
        self.dlg_informe3 = GenerarInforme3()
        self.dlg_listar_construccion_plantas = ListarConstruccionPlantas(parent=self.iface.mainWindow(), db_driver=self.driver)
        
        self.dlg_listar_construccion_plantas = ListarConstruccionPlantas()
        
        self.dlg_export_especial = ExportDatabaseEspecial()
        self.dlg_export_mejora = ExportDatabaseMejoras()
        self.dlg_export_planta = ExportDatabasePlantas()
        
        
        self.dlg_select_titular = SelectTitular()
        self.dlg_select_titular_feature = SelectTitularFeature()
        
        
        self.dlg_select_titular_busca_ref = SelectTitularBuscaRef()
        self.dlg_select_titular_busca_nombre = SelectTitularBuscaNombre()
        
        self.dlg_select_titular_feature_busca_ref = SelectTitularFeatureBuscaRef()
        self.dlg_select_titular_feature_busca_nombre = SelectTitularFeatureBuscaNombre()
        
        self.dlg_select_construccion_planta_busca_ref = SelectConstruccionPlantaBuscaRef()
        
        self.dlg_select_terreno_layout_busca_ref = SelectTerrenoLayoutBuscaRef()
        self.dlg_select_terreno_layout_busca_nombre = SelectTerrenoLayoutBuscaNombre()
        
        self.dlg_select_terreno_informe_busca_ref = SelectTerrenoInformeBuscaRef()
        self.dlg_select_terreno_informe_busca_nombre = SelectTerrenoInformeBuscaNombre()
 
        self.dlg_select_terreno_informe2_busca_ref = SelectTerrenoInforme2BuscaRef()
        self.dlg_select_terreno_informe2_busca_nombre = SelectTerrenoInforme2BuscaNombre() 
        
        self.dlg_select_terreno_informe3_busca_ref = SelectTerrenoInforme3BuscaRef()
        self.dlg_select_terreno_informe3_busca_nombre = SelectTerrenoInforme3BuscaNombre()
        
        
        self.dlg_guardar_feature_cambiar_titular = GuardarFeatureCambioTitular()
        self.dlg_select_titular_cambio_titular = SelecTitularCambioTitular()
        self.dlg_select_titular_cambio_titular_busca_ref = SelectTitularCambioTitularBuscaRef()
        self.dlg_select_titular_cambio_titular_busca_nombre = SelectTitularCambioTitularBuscaNombre()
        self.confirmar_guardar_titular = ConfirmarGuardarTitular()
        
        self.dlg_guardar_feature_union = GuardarFeatureUnion()
        self.dlg_select_titular_union = SelecTitularUnion()
        self.dlg_select_titular_union_busca_ref = SelectTitularUnionBuscaRef()
        self.dlg_select_titular_union_busca_nombre = SelectTitularUnionBuscaNombre()
        self.dlg_confirmar_union = ConfirmarUnion()   
        
        
        self.dlg_info_forma_union = InfoFormaUnion()
        self.dlg_info_inclinacion_union = InfoInclinacionUnion()
        self.dlg_info_material_calzada_union = InfoMaterialCalzadaUnion()
        self.dlg_info_tipo_calzada_union = InfoTipoCalzadaUnion()
        self.dlg_info_ubicacion_union = InfoUbicacionUnion()
        self.dlg_info_codigo_union = InfoCodigoUnion()
        self.dlg_info_zona_union = InfoZonaUnion()
        
 

        self.dlg_guardar_feature_divide = GuardarFeatureDivide()
        self.dlg_guardar_linea_divide = GuardarLineaDivide()
        self.dlg_select_titular_divide1 = SelecTitularDivide1()
        self.dlg_select_titular_divide2 = SelecTitularDivide2()
        self.dlg_select_titular_divide1_buscar_ref = SelectTitularDivide1BuscaRef()
        self.dlg_select_titular_divide2_buscar_ref = SelectTitularDivide2BuscaRef()
        self.dlg_select_titular_divide1_buscar_nombre = SelectTitularDivide1BuscaNombre()
        self.dlg_select_titular_divide2_buscar_nombre = SelectTitularDivide2BuscaNombre()
        self.dlg_confirmar_divide = ConfirmarDivide()
        
        self.dlg_info_codigo_divide1 = InfoCodigoDivide1()
        self.dlg_info_codigo_divide2 = InfoCodigoDivide2()

 
        
        #################################CAMBIO TITULOS EN DIALOGS#####################################################################
        
        
        self.dlg_export_titular.setWindowTitle("Carga Datos del Titular de la Parcela en la Base de Datos")
        self.dlg_listar_titular.setWindowTitle("Buscar Titulares")
        
        self.dlg_export.setWindowTitle("Carga Datos de la Parcela en la Base de Datos")
        self.dlg_informe.setWindowTitle("Selecciona una Parcela y Genera un Informe")
        self.dlg_huso.setWindowTitle("Selecciona Huso Horario")
        self.dlg_guardar_feature.setWindowTitle("Selecciona un Polígono")

        self.dlg_guardar_ejevia.setWindowTitle('Seleccione un Manzano')
        self.dlg_guardar_ejevia.label.setText('Selecciona un Manzano a Continuación haz click en Guardar Seleccion o Cancelar ')
        
        self.dlg_huso.setWindowTitle("Selecciona un Huso Horario")
        self.dlg_huso_feature.setWindowTitle("Selecciona un Huso Horario")
        self.dlg_export_feature.setWindowTitle("Carga Datos de la Parcela Seleccionada en la Base de Datos")
        
        self.dlg_guardar_feature_construccion.setWindowTitle("Selecciona un Polígono")
        self.dlg_huso_feature_construccion.setWindowTitle("Selecciona un Huso Horario")
        self.dlg_export_feature_construccion.setWindowTitle("Carga Datos de la Construcción Seleccionada en la Base de Datos")
        
        self.dlg_huso_layout.setWindowTitle("Selecciona Huso Horario")
        self.dlg_layout.setWindowTitle("Selecciona una Parcela y Genera un Plano")
        
        self.dlg_huso_informe.setWindowTitle("Selecciona Huso Horario")
        self.dlg_huso_informe2.setWindowTitle("Selecciona Huso Horario")
        self.dlg_huso_informe3.setWindowTitle("Selecciona Huso Horario")
        
        self.dlg_informe2.setWindowTitle("Selecciona una Parcela y Genera un Informe")
        self.dlg_informe3.setWindowTitle("Selecciona una Parcela")
        
        self.dlg_listar_construccion_plantas.setWindowTitle("Selecciona una Construcción y Genera un Informe")
        
        self.dlg_export_especial.setWindowTitle("Carga Nueva Edficación Especial")
        self.dlg_export_mejora.setWindowTitle("Carga Nueva Mejora")
        self.dlg_export_planta.setWindowTitle("Carga Nueva Planta")
        
        
        self.dlg_select_titular.setWindowTitle("Selecciona Titular del Terreno")
        self.dlg_select_titular_feature.setWindowTitle("Selecciona Titular del Terreno")
        
        
        self.dlg_select_titular_busca_ref.setWindowTitle("Ingresa un Documento")
        self.dlg_select_titular_busca_nombre.setWindowTitle("Ingresa un Nombre y/o Apellidos")
        
        self.dlg_select_titular_feature_busca_ref.setWindowTitle("Ingresa un Documento")
        self.dlg_select_titular_feature_busca_nombre.setWindowTitle("Ingresa un Nombre y/o Apellidos")
        
        
        self.dlg_listar_construccion_plantas.setWindowTitle("Selecciona una Construcción")
        
        
        self.dlg_select_terreno_layout_busca_ref.setWindowTitle("Ingesa Código Catastral")
        self.dlg_select_terreno_layout_busca_nombre.setWindowTitle("Ingesa un Nombre y/o Apellidos")


        self.dlg_select_terreno_informe_busca_ref.setWindowTitle("Ingesa Código Catastral")
        self.dlg_select_terreno_informe_busca_nombre.setWindowTitle("Ingesa un Nombre y/o Apellidos")


        self.dlg_select_terreno_informe2_busca_ref.setWindowTitle("Ingesa Código Catastral")
        self.dlg_select_terreno_informe2_busca_nombre.setWindowTitle("Ingesa un Nombre y/o Apellidos")

        
        self.dlg_select_terreno_informe3_busca_ref.setWindowTitle("Ingesa Código Catastral")
        self.dlg_select_terreno_informe3_busca_nombre.setWindowTitle("Ingesa un Nombre y/o Apellidos")
        
        
        self.dlg_guardar_feature_cambiar_titular.setWindowTitle("Selecciona Un Terreno")
        self.dlg_select_titular_cambio_titular.setWindowTitle("Selecciona el Nuevo Titular")
        self.dlg_select_titular_cambio_titular_busca_ref.setWindowTitle("Ingresa un Documento")
        self.dlg_select_titular_cambio_titular_busca_nombre.setWindowTitle("Ingresa un Nombre y/o Apellidos")
        self.confirmar_guardar_titular.setWindowTitle("Cambio de Titular")
        
        
        self.dlg_guardar_feature_union.setWindowTitle("Selecciona Dos Terrenos Contiguos")
        self.dlg_select_titular_union.setWindowTitle("Selecciona el Nuevo Titular")
        self.dlg_select_titular_union_busca_ref.setWindowTitle("Ingresa un Documento")
        self.dlg_select_titular_union_busca_nombre.setWindowTitle("Ingresa un Nombre y/o Apellidos")
        self.dlg_confirmar_union.setWindowTitle("Unir Dos Terrenos") 



        self.dlg_info_forma_union.setWindowTitle("Selecciona Dos Terrenos Contiguos")
        self.dlg_info_inclinacion_union.setWindowTitle("Selecciona Dos Terrenos Contiguos")
        self.dlg_info_material_calzada_union.setWindowTitle("Selecciona Dos Terrenos Contiguos")
        self.dlg_info_tipo_calzada_union.setWindowTitle("Selecciona Dos Terrenos Contiguos")
        self.dlg_info_ubicacion_union.setWindowTitle("Selecciona Dos Terrenos Contiguos")
        self.dlg_info_codigo_union.setWindowTitle("Selecciona Dos Terrenos Contiguos")
        self.dlg_info_zona_union.setWindowTitle("Selecciona Dos Terrenos Contiguos")



        self.dlg_guardar_feature_divide.setWindowTitle("Selecciona Un Terreno")
        self.dlg_guardar_linea_divide.setWindowTitle("Selecciona Una Linea de División")
        self.dlg_select_titular_divide1.setWindowTitle("Selecciona Titular del Terreno de la Izqda")
        self.dlg_select_titular_divide2.setWindowTitle("Selecciona Titular del Terreno de la Drcha")
        self.dlg_select_titular_divide1_buscar_ref.setWindowTitle("Ingresa un Documento")
        self.dlg_select_titular_divide2_buscar_ref.setWindowTitle("Ingresa un Documento")
        self.dlg_select_titular_divide1_buscar_nombre.setWindowTitle("Ingresa un Nombre y/o Apellidos")
        self.dlg_select_titular_divide2_buscar_nombre.setWindowTitle("Ingresa un Nombre y/o Apellidos")
        self.dlg_confirmar_divide.setWindowTitle("Divide el Terreno")
        
        self.dlg_info_codigo_divide1.setWindowTitle("Ingresa el nuevo Codigo y Dirección")
        self.dlg_info_codigo_divide2.setWindowTitle("Ingresa el nuevo Codigo y Dirección")


        
        #########################################################################################################
        ################################ FUNCIONES CARGA BOTONES #################################################
        
        
        
        ##################################################### PRIMER BOTON CARGA TITULAR ############################################################ 
        


        
        # self.dlg_export_titular.btn_cancelar_prop.clicked.connect(self.cerrar_dialogo_exportartitular)  
        # self.dlg_export_titular.btn_update_prop.clicked.connect(self.abrir_dialogo_titulares)  
        
        
        self.dlg_export_titular.btn_guardar_prop.clicked.connect(self.guardar_titular)
        # self.dlg_export_titular.btn_guardar_prop.clicked.connect(self.abrir_dialogo_exportbbdd)
        # self.dlg_export_titular.btn_guardar_prop.clicked.connect(self.cerrar_dialogo_exportartitular)
   
      
               
                
                
 
        ##################################################### BOTON CARGA CSV Y GUARDA ############################################################  
        
        self.dlg_select_titular.btn_select_titular.clicked.connect(self.abrir_dialogo_exportbbdd)
        self.dlg_select_titular.btn_select_titular.clicked.connect(self.cerrar_dialogo_listar_titular)
        
        self.dlg_select_titular.btn_titular_selec_ref.clicked.connect(self.abrir_dialogo_listar_titular_buscar_ref)
  
  
        self.dlg_select_titular_busca_ref.btn_busca.clicked.connect(self.titular_busca_ref)
        self.dlg_select_titular_busca_ref.btn_busca.clicked.connect(self.cerrar_dialogo_listar_titular_buscar_ref)
        
        
        
        self.dlg_select_titular_busca_ref.btn_aceptar.clicked.connect(self.cerrar_dialogo_listar_titular_buscar_ref)
        self.dlg_select_titular_busca_ref.btn_cancelar.clicked.connect(self.cerrar_dialogo_listar_titular_buscar_ref)
        
        
        self.dlg_select_titular.btn_titular_selec_nombre.clicked.connect(self.abrir_dialogo_listar_titular_buscar_nombre)
        
        
        self.dlg_select_titular_busca_nombre.btn_busca.clicked.connect(self.titular_busca_nombre)
        self.dlg_select_titular_busca_nombre.btn_busca.clicked.connect(self.cerrar_dialogo_listar_titular_buscar_nombre)
        
        
        self.dlg_select_titular_busca_nombre.btn_aceptar.clicked.connect(self.cerrar_dialogo_listar_titular_buscar_nombre)
        self.dlg_select_titular_busca_nombre.btn_cancelar.clicked.connect(self.cerrar_dialogo_listar_titular_buscar_nombre)
        
        
        self.dlg_select_titular.btn_titular_limpiar.clicked.connect(self.cargar_titular)
                 
        
        
        self.dlg.btn_guardarbbdd.clicked.connect(self.abrir_dialogo_listar_titular)
        self.dlg.btn_guardarbbdd.clicked.connect(self.cargar_titular)
        self.dlg.btn_guardarbbdd.clicked.connect(self.cerrar_dialogo_cargacsv)
        
               

        
        
 
        
        self.dlg_export.btn_exportdb.clicked.connect(self.cargar_csv)
        self.dlg_export.btn_exportdb.clicked.connect(self.cerrar_dialogo_exportbbdd)
        
        
        
        ##################################################### SEGUNDO BOTON SELCCIONA FEATURE Y GUARDA ############################################################
        
        self.dlg_guardar_feature.btn_guardar.clicked.connect(self.abrir_dialogo_listar_titular_feature)
        self.dlg_guardar_feature.btn_guardar.clicked.connect(self.cargar_titular_feature)
        self.dlg_guardar_feature.btn_guardar.clicked.connect(self.cerrar_dialogo_guardarfeature)


        self.dlg_guardar_ejevia.btn_guardar.clicked.connect(self.ejes_de_vias) #! OJO AQUI
        self.dlg_guardar_ejevia.btn_guardar.clicked.connect(self.cerrar_dialog_guardar_ejevias) #! OJO AQUI

        self.dlg_guardar_ejevia.btn_cancelar.clicked.connect(self.cerrar_dialog_guardar_ejevias)
        self.dlg_guardar_ejevia.btn_cancelar.clicked.connect(self.desactiva_seleccion)
        
        self.dlg_guardar_feature.btn_cancelar.clicked.connect(self.cerrar_dialogo_guardarfeature)
        self.dlg_guardar_feature.btn_cancelar.clicked.connect(self.desactiva_seleccion)
        self.dlg_guardar_feature.btn_cancelar.clicked.connect(self.cerrar_dialogo_listar_titular_feature)
        
        
        
        
        self.dlg_select_titular_feature.btn_select_titular.clicked.connect(self.abrir_dialogo_exportbbdd_feature)
        self.dlg_select_titular_feature.btn_select_titular.clicked.connect(self.cerrar_dialogo_listar_titular_feature)
        
        
        self.dlg_select_titular_feature.btn_titular_selec_ref.clicked.connect(self.abrir_dialogo_listar_titular_feature_buscar_ref)
        self.dlg_select_titular_feature.btn_titular_selec_nombre.clicked.connect(self.abrir_dialogo_listar_titular_feature_buscar_nombre)
        self.dlg_select_titular_feature.btn_titular_limpiar.clicked.connect(self.cargar_titular_feature)
        
        
        
        self.dlg_select_titular_feature_busca_ref.btn_busca.clicked.connect(self.titular_feature_busca_ref)
        self.dlg_select_titular_feature_busca_ref.btn_busca.clicked.connect(self.cerrar_dialogo_listar_titular_feature_buscar_ref)
       
        
        self.dlg_select_titular_feature_busca_ref.btn_aceptar.clicked.connect(self.cerrar_dialogo_listar_titular_feature_buscar_ref)
        self.dlg_select_titular_feature_busca_ref.btn_cancelar.clicked.connect(self.cerrar_dialogo_listar_titular_feature_buscar_ref)
        
        
        self.dlg_select_titular_feature_busca_nombre.btn_busca.clicked.connect(self.titular_feature_busca_nombre)
        self.dlg_select_titular_feature_busca_nombre.btn_busca.clicked.connect(self.cerrar_dialogo_listar_titular_feature_buscar_nombre)
        
        
        self.dlg_select_titular_feature_busca_nombre.btn_aceptar.clicked.connect(self.cerrar_dialogo_listar_titular_feature_buscar_nombre)
        self.dlg_select_titular_feature_busca_nombre.btn_cancelar.clicked.connect(self.cerrar_dialogo_listar_titular_feature_buscar_nombre)
               
        
        self.dlg_export_feature.btn_exportdb.clicked.connect(self.selecciona_feature)
        self.dlg_export_feature.btn_exportdb.clicked.connect(self.cerrar_dialogo_exportbbdd_feature)
        
        
        
   
        
        ##################################################### CARGA Y GUARDA DATOS DEL TITULAR DESDE SELECCION ############################################################  
        
        # self.dlg_export_titular_feature.btn_guardar_prop.clicked.connect(self.guardar_titular_feature)
        # self.dlg_export_titular_feature.btn_guardar_prop.clicked.connect(self.abrir_dialogo_exportbbdd_feature)
        # self.dlg_export_titular_feature.btn_guardar_prop.clicked.connect(self.cerrar_dialogo_exportartitular_feature)
   
      
        # self.dlg_export_titular_feature.btn_cancelar_prop.clicked.connect(self.cerrar_dialogo_exportartitular_feature)
 


        ##################################################### TERCER BOTON SELCCIONA CONSTRUCCION Y GUARDA ####################################################
        self.dlg_export_feature_construccion.pushButton.clicked.connect(self.referenciar_construccion)
        
        self.dlg_guardar_feature_construccion.btn_guardar.clicked.connect(self.abrir_dialogo_exportbbdd_feature_construccion)
        self.dlg_guardar_feature_construccion.btn_guardar.clicked.connect(self.cargar_tablabbdd_construccion)
        self.dlg_guardar_feature_construccion.btn_guardar.clicked.connect(self.cerrar_dialogo_guardarfeature_construccion)

                
        self.dlg_guardar_feature_construccion.btn_cancelar.clicked.connect(self.cerrar_dialogo_guardarfeature_construccion)
        self.dlg_guardar_feature_construccion.btn_cancelar.clicked.connect(self.desactiva_seleccion)
        
        
        self.dlg_export_feature_construccion.btn_exportdb.clicked.connect(self.cerrar_dialogo_exportbbdd_feature_construccion)
        self.dlg_export_feature_construccion.btn_exportdb.clicked.connect(self.selecciona_construccion)
        
        self.dlg_export_feature_construccion.btn_exportdb_esp.clicked.connect(self.abrir_dialogo_exportbbdd_especiales)
        
        self.dlg_export_feature_construccion.btn_exportdb_esp.clicked.connect(self.cargar_tablabbdd_especial)
        
        
        self.dlg_export_feature_construccion.btn_exportdb_mejora.clicked.connect(self.abrir_dialogo_exportbbdd_mejoras)
        self.dlg_export_feature_construccion.btn_exportdb_mejora.clicked.connect(self.cargar_tablabbdd_mejora)
 

        self.dlg_export_especial.btn_cancelar.clicked.connect(self.cerrar_dialogo_exportbbdd_especiales)
        
        self.dlg_export_especial.btn_guardar.clicked.connect(self.cerrar_dialogo_exportbbdd_especiales)
        self.dlg_export_especial.btn_guardar.clicked.connect(self.guardar_feature_bbdd_especial)  


        self.dlg_export_mejora.btn_cancelar.clicked.connect(self.cerrar_dialogo_exportbbdd_mejoras)
        
        self.dlg_export_mejora.btn_guardar.clicked.connect(self.cerrar_dialogo_exportbbdd_mejoras)
        self.dlg_export_mejora.btn_guardar.clicked.connect(self.guardar_feature_bbdd_mejora)         
        
        
        ###################################################    BOTON PLANTAS Y MATERIALES       ########################################################
        
        
        self.dlg_listar_construccion_plantas.btn_informe.clicked.connect(self.abrir_dialogo_exportbbdd_planta)
        self.dlg_listar_construccion_plantas.btn_informe.clicked.connect(self.cerrar_dialogo_listarconstruccion_plantas)
        
        
        self.dlg_listar_construccion_plantas.btn_const_selec_ref.clicked.connect(self.abrir_dialogo_select_construccion_planta_busca_ref)
        self.dlg_listar_construccion_plantas.btn_const_limpiar.clicked.connect(self.cargar_tablaconstruccionbd_plantas)
        
        
        self.dlg_select_construccion_planta_busca_ref.btn_busca.clicked.connect(self.planta_busca_ref)
        self.dlg_select_construccion_planta_busca_ref.btn_busca.clicked.connect(self.cerrar_dialogo_select_construccion_planta_busca_ref)
        
        self.dlg_select_construccion_planta_busca_ref.btn_cancelar.clicked.connect(self.cerrar_dialogo_select_construccion_planta_busca_ref)
        self.dlg_select_construccion_planta_busca_ref.btn_aceptar.clicked.connect(self.cerrar_dialogo_select_construccion_planta_busca_ref)
        
        #self.dlg_export_planta = ExportDatabasePlantas()
        #self.dlg_export_planta.btn_guardar.clicked.connect(self.cerrar_dialogo_exportbbdd_planta)
        
        
      
        
        #self.dlg_export_planta.btn_cancelar.clicked.connect(self.cerrar_dialogo_exportbbdd_planta)
        
        
        
        
        ##################################################### CUARTO BOTON DIBUJA LAYOUT ####################################################


               
        self.dlg_layout.btn_layout.clicked.connect(self.mostrar_layout)
        self.dlg_layout.btn_layout.clicked.connect(self.cerrar_dialogo_layout)
        
        self.dlg_layout.btn_selec_ref.clicked.connect(self.abrir_select_terreno_layout_busca_ref)
        self.dlg_layout.btn_selec_nombre.clicked.connect(self.abrir_select_terreno_layout_busca_nombre)
        self.dlg_layout.btn_limpiar.clicked.connect(self.cargar_tablabbdd)
        
        
        self.dlg_select_terreno_layout_busca_ref.btn_busca.clicked.connect(self.listar_layer_busca_ref)
        self.dlg_select_terreno_layout_busca_ref.btn_busca.clicked.connect(self.cerrar_select_terreno_layout_busca_ref)
        
        self.dlg_select_terreno_layout_busca_ref.btn_aceptar.clicked.connect(self.cerrar_select_terreno_layout_busca_ref)
        self.dlg_select_terreno_layout_busca_ref.btn_cancelar.clicked.connect(self.cerrar_select_terreno_layout_busca_ref)
        
        
        self.dlg_select_terreno_layout_busca_nombre.btn_busca.clicked.connect(self.listar_layer_busca_nombre)
        self.dlg_select_terreno_layout_busca_nombre.btn_busca.clicked.connect(self.cerrar_select_terreno_layout_busca_nombre)
        
        self.dlg_select_terreno_layout_busca_nombre.btn_aceptar.clicked.connect(self.cerrar_select_terreno_layout_busca_nombre)
        self.dlg_select_terreno_layout_busca_nombre.btn_cancelar.clicked.connect(self.cerrar_select_terreno_layout_busca_nombre)
    
        

        ##################################################### QUINTO BOTON PRIMER CERTIFICADO ####################################################

        
        self.dlg_informe.btn_informe.clicked.connect(self.mostrar_informe)
        self.dlg_informe.btn_informe.clicked.connect(self.cerrar_dialogo_informe)
        
        self.dlg_informe.btn_selec_ref.clicked.connect(self.abrir_dialogo_select_terreno_informe_busca_ref)
        self.dlg_informe.btn_selec_nombre.clicked.connect(self.abrir_dialogo_select_terreno_informe_busca_nombre)
        self.dlg_informe.btn_limpiar.clicked.connect(self.cargar_tablabbdd2)
        

        self.dlg_select_terreno_informe_busca_ref.btn_busca.clicked.connect(self.listar_layer_informe_busca_ref)
        self.dlg_select_terreno_informe_busca_ref.btn_busca.clicked.connect(self.cerrar_dialogo_select_terreno_informe_busca_ref)
 

        self.dlg_select_terreno_informe_busca_ref.btn_aceptar.clicked.connect(self.cerrar_dialogo_select_terreno_informe_busca_ref)
        self.dlg_select_terreno_informe_busca_ref.btn_cancelar.clicked.connect(self.cerrar_dialogo_select_terreno_informe_busca_ref)


        self.dlg_select_terreno_informe_busca_nombre.btn_busca.clicked.connect(self.listar_layer_informe_busca_nombre)
        self.dlg_select_terreno_informe_busca_nombre.btn_busca.clicked.connect(self.cerrar_dialogo_select_terreno_informe_busca_nombre)

        self.dlg_select_terreno_informe_busca_nombre.btn_aceptar.clicked.connect(self.cerrar_dialogo_select_terreno_informe_busca_nombre)
        self.dlg_select_terreno_informe_busca_nombre.btn_cancelar.clicked.connect(self.cerrar_dialogo_select_terreno_informe_busca_nombre)       
       
        ##################################################### SEXTO BOTON SEGUNDO CERTIFICADO ####################################################
        #BOTON DE CERTIFICADO CATASTRAL
        
        
        self.dlg_informe2.btn_informe.clicked.connect(self.mostrar_informe2)
        self.dlg_informe2.btn_informe.clicked.connect(self.cerrar_dialogo_informe2)
        
        self.dlg_informe2.btn_selec_ref.clicked.connect(self.abrir_dialogo_select_terreno_informe2_busca_ref)
        self.dlg_informe2.btn_selec_nombre.clicked.connect(self.abrir_dialogo_select_terreno_informe2_busca_nombre)
        self.dlg_informe2.btn_limpiar.clicked.connect(self.cargar_tablabbdd3)
        

        self.dlg_select_terreno_informe2_busca_ref.btn_busca.clicked.connect(self.listar_layer_informe2_busca_ref)
        self.dlg_select_terreno_informe2_busca_ref.btn_busca.clicked.connect(self.cerrar_dialogo_select_terreno_informe2_busca_ref)
 

        self.dlg_select_terreno_informe2_busca_ref.btn_aceptar.clicked.connect(self.cerrar_dialogo_select_terreno_informe2_busca_ref)
        self.dlg_select_terreno_informe2_busca_ref.btn_cancelar.clicked.connect(self.cerrar_dialogo_select_terreno_informe2_busca_ref)


        self.dlg_select_terreno_informe2_busca_nombre.btn_busca.clicked.connect(self.listar_layer_informe2_busca_nombre)
        self.dlg_select_terreno_informe2_busca_nombre.btn_busca.clicked.connect(self.cerrar_dialogo_select_terreno_informe2_busca_nombre)

        self.dlg_select_terreno_informe2_busca_nombre.btn_aceptar.clicked.connect(self.cerrar_dialogo_select_terreno_informe2_busca_nombre)
        self.dlg_select_terreno_informe2_busca_nombre.btn_cancelar.clicked.connect(self.cerrar_dialogo_select_terreno_informe2_busca_nombre)  
       
        ##################################################### SEPTIMO BOTON TERCER CERTIFICADO ####################################################
        #BOTON DE CERTIFICADO AVALUO
        
        
        
        self.dlg_informe3.btn_informe.clicked.connect(self.mostrar_informe3)
        self.dlg_informe3.btn_informe.clicked.connect(self.cerrar_dialogo_informe3)
 


        self.dlg_informe3.btn_selec_ref.clicked.connect(self.abrir_dialogo_select_terreno_informe3_busca_ref)
        self.dlg_informe3.btn_selec_nombre.clicked.connect(self.abrir_dialogo_select_terreno_informe3_busca_nombre)
        self.dlg_informe3.btn_limpiar.clicked.connect(self.cargar_tablabbdd4)
        

        self.dlg_select_terreno_informe3_busca_ref.btn_busca.clicked.connect(self.listar_layer_informe3_busca_ref)
        self.dlg_select_terreno_informe3_busca_ref.btn_busca.clicked.connect(self.cerrar_dialogo_select_terreno_informe3_busca_ref)
 

        self.dlg_select_terreno_informe3_busca_ref.btn_aceptar.clicked.connect(self.cerrar_dialogo_select_terreno_informe3_busca_ref)
        self.dlg_select_terreno_informe3_busca_ref.btn_cancelar.clicked.connect(self.cerrar_dialogo_select_terreno_informe3_busca_ref)


        self.dlg_select_terreno_informe3_busca_nombre.btn_busca.clicked.connect(self.listar_layer_informe3_busca_nombre)
        self.dlg_select_terreno_informe3_busca_nombre.btn_busca.clicked.connect(self.cerrar_dialogo_select_terreno_informe3_busca_nombre)

        self.dlg_select_terreno_informe3_busca_nombre.btn_aceptar.clicked.connect(self.cerrar_dialogo_select_terreno_informe3_busca_nombre)
        self.dlg_select_terreno_informe3_busca_nombre.btn_cancelar.clicked.connect(self.cerrar_dialogo_select_terreno_informe3_busca_nombre) 


 
        self.dlg_listar_construccion_plantas.btn_informe.clicked.connect(self.mostrar_informe3)
        self.dlg_listar_construccion_plantas.btn_informe.clicked.connect(self.cerrar_dialogo_listarconstruccion_plantas)
        
        
        ##################################################### CAMBIO DE TITULAR ####################################################
        
        self.dlg_guardar_feature_cambiar_titular.btn_guardar.clicked.connect(self.cerrar_dialogo_guardarfeature_cambiarTitular)
        self.dlg_guardar_feature_cambiar_titular.btn_guardar.clicked.connect(self.abrir_select_titular_cambio_titular)
        self.dlg_guardar_feature_cambiar_titular.btn_guardar.clicked.connect(self.cargar_titular_cambiar_titular)
        
        self.dlg_guardar_feature_cambiar_titular.btn_cancelar.clicked.connect(self.cerrar_dialogo_guardarfeature_cambiarTitular)
        
        
        self.dlg_select_titular_cambio_titular.btn_titular_selec_nombre.clicked.connect(self.abrir_select_titular_cambio_titular_busca_nombre)
        self.dlg_select_titular_cambio_titular.btn_titular_selec_ref.clicked.connect(self.abrir_select_titular_cambio_titular_busca_ref)
        self.dlg_select_titular_cambio_titular.btn_titular_limpiar.clicked.connect(self.cargar_titular_cambiar_titular)
        self.dlg_select_titular_cambio_titular.btn_select_titular.clicked.connect(self.abrir_confirmar_guardar_titular)
        self.dlg_select_titular_cambio_titular.btn_select_titular.clicked.connect(self.cerrar_select_titular_cambio_titular)
        
                      
        self.dlg_select_titular_cambio_titular_busca_nombre.btn_cancelar.clicked.connect(self.cerrar_select_titular_cambio_titular_busca_nombre)
        self.dlg_select_titular_cambio_titular_busca_nombre.btn_aceptar.clicked.connect(self.cerrar_select_titular_cambio_titular_busca_nombre)
        self.dlg_select_titular_cambio_titular_busca_nombre.btn_busca.clicked.connect(self.titular_titular_cambiar_busca_nombre)
        
        
        self.dlg_select_titular_cambio_titular_busca_ref.btn_cancelar.clicked.connect(self.cerrar_select_titular_cambio_titular_busca_ref)
        self.dlg_select_titular_cambio_titular_busca_ref.btn_aceptar.clicked.connect(self.cerrar_select_titular_cambio_titular_busca_ref)
        self.dlg_select_titular_cambio_titular_busca_ref.btn_busca.clicked.connect(self.titular_titular_cambiar_busca_ref)
        
                
        self.confirmar_guardar_titular.btn_cancelar.clicked.connect(self.cerrar_confirmar_guardar_titular)
        self.confirmar_guardar_titular.btn_cancelar.clicked.connect(self.abrir_select_titular_cambio_titular)
    
        self.confirmar_guardar_titular.btn_guardar.clicked.connect(self.cerrar_confirmar_guardar_titular)
        self.confirmar_guardar_titular.btn_guardar.clicked.connect(self.cambia_titular)
        
        
        
    ################################################################### UNIÓN DE DOS PARCELAS ################################################################

        self.dlg_guardar_feature_union.btn_guardar.clicked.connect(self.cerrar_guardar_feature_union)
        self.dlg_guardar_feature_union.btn_guardar.clicked.connect(self.abrir_select_titular_union)
        self.dlg_guardar_feature_union.btn_guardar.clicked.connect(self.cargar_titular_union)
        
        self.dlg_guardar_feature_union.btn_cancelar.clicked.connect(self.cerrar_guardar_feature_union)
        
        
        self.dlg_select_titular_union.btn_titular_selec_nombre.clicked.connect(self.abrir_select_titular_union_busca_nombre)
        self.dlg_select_titular_union.btn_titular_selec_ref.clicked.connect(self.abrir_select_titular_union_busca_ref)
        self.dlg_select_titular_union.btn_titular_limpiar.clicked.connect(self.cargar_titular_union)
        self.dlg_select_titular_union.btn_select_titular.clicked.connect(self.abrir_dlg_info_codigo_union_union)
        self.dlg_select_titular_union.btn_select_titular.clicked.connect(self.cerrar_select_titular_union)
        
        
        self.dlg_select_titular_union_busca_nombre.btn_cancelar.clicked.connect(self.cerrar_select_titular_union_busca_nombre)
        self.dlg_select_titular_union_busca_nombre.btn_aceptar.clicked.connect(self.cerrar_select_titular_union_busca_nombre)
        self.dlg_select_titular_union_busca_nombre.btn_busca.clicked.connect(self.titular_union_busca_nombre)
        
        
        self.dlg_select_titular_union_busca_ref.btn_cancelar.clicked.connect(self.cerrar_select_titular_union_busca_ref)
        self.dlg_select_titular_union_busca_ref.btn_aceptar.clicked.connect(self.cerrar_select_titular_union_busca_ref)
        self.dlg_select_titular_union_busca_ref.btn_busca.clicked.connect(self.titular_union_busca_ref)
        
        
        self.dlg_info_codigo_union.btn_guardar.clicked.connect(self.abrir_confirmar_union)
        self.dlg_info_codigo_union.btn_guardar.clicked.connect(self.cerrar_dlg_info_codigo_union_union)
        self.dlg_info_codigo_union.btn_cancelar.clicked.connect(self.cerrar_dlg_info_codigo_union_union)
        
        
        self.dlg_confirmar_union.btn_cancelar.clicked.connect(self.cerrar_confirmar_union)
        self.dlg_confirmar_union.btn_cancelar.clicked.connect(self.abrir_select_titular_union)
        self.dlg_confirmar_union.btn_guardar.clicked.connect(self.cerrar_confirmar_union)
        self.dlg_confirmar_union.btn_guardar.clicked.connect(self.union_titular)

################################################################## DIVIDIR  PARCELA ################################################################



   
        self.dlg_guardar_feature_divide.btn_guardar.clicked.connect(self.cerrar_guardar_feature_divide)
        self.dlg_guardar_feature_divide.btn_guardar.clicked.connect(self.abrir_guardar_linea_divide)
        self.dlg_guardar_feature_divide.btn_guardar.clicked.connect(self.guardar_terreno)
        self.dlg_guardar_feature_divide.btn_cancelar.clicked.connect(self.cerrar_guardar_feature_union)
        
        self.dlg_guardar_linea_divide.btn_guardar.clicked.connect(self.cerrar_guardar_linea_divide)
        self.dlg_guardar_linea_divide.btn_guardar.clicked.connect(self.cerrar_guardar_linea_divide)
        self.dlg_guardar_linea_divide.btn_guardar.clicked.connect(self.abrir_select_titular_divide1)
        self.dlg_guardar_linea_divide.btn_guardar.clicked.connect(self.cargar_titular_divide1)
        self.dlg_guardar_linea_divide.btn_guardar.clicked.connect(self.guardar_linea)
        self.dlg_guardar_linea_divide.btn_cancelar.clicked.connect(self.cerrar_guardar_linea_divide)
        
        
        self.dlg_select_titular_divide1.btn_titular_selec_nombre.clicked.connect(self.abrir_select_titular_divide1_buscar_nombre)
        self.dlg_select_titular_divide1.btn_titular_selec_ref.clicked.connect(self.abrir_select_titular_divide1_buscar_ref)
        self.dlg_select_titular_divide1.btn_titular_limpiar.clicked.connect(self.cargar_titular_divide1)
        self.dlg_select_titular_divide1.btn_select_titular.clicked.connect(self.abrir_dlg_info_codigo_divide1)
        self.dlg_select_titular_divide1.btn_select_titular.clicked.connect(self.cerrar_select_titular_divide1)
        
        
        self.dlg_select_titular_divide1_buscar_nombre.btn_cancelar.clicked.connect(self.cerrar_select_titular_divide1_buscar_nombre)
        self.dlg_select_titular_divide1_buscar_nombre.btn_aceptar.clicked.connect(self.cerrar_select_titular_divide1_buscar_nombre)
        self.dlg_select_titular_divide1_buscar_nombre.btn_busca.clicked.connect(self.titular_divide1_busca_nombre)
        
        
        self.dlg_select_titular_divide1_buscar_ref.btn_cancelar.clicked.connect(self.cerrar_select_titular_divide1_buscar_ref)
        self.dlg_select_titular_divide1_buscar_ref.btn_aceptar.clicked.connect(self.cerrar_select_titular_divide1_buscar_ref)
        self.dlg_select_titular_divide1_buscar_ref.btn_busca.clicked.connect(self.titular_divide1_busca_ref)
        
        

        self.dlg_info_codigo_divide1.btn_guardar.clicked.connect(self.abrir_select_titular_divide2)
        self.dlg_info_codigo_divide1.btn_guardar.clicked.connect(self.cargar_titular_divide2)
        self.dlg_info_codigo_divide1.btn_guardar.clicked.connect(self.cerrar_dlg_info_codigo_divide1)
        self.dlg_info_codigo_divide1.btn_cancelar.clicked.connect(self.cerrar_dlg_info_codigo_divide1)



        self.dlg_select_titular_divide2.btn_titular_selec_nombre.clicked.connect(self.abrir_select_titular_divide2_buscar_nombre)
        self.dlg_select_titular_divide2.btn_titular_selec_ref.clicked.connect(self.abrir_select_titular_divide2_buscar_ref)
        self.dlg_select_titular_divide2.btn_titular_limpiar.clicked.connect(self.cargar_titular_divide2)
        self.dlg_select_titular_divide2.btn_select_titular.clicked.connect(self.abrir_dlg_info_codigo_divide2)
        self.dlg_select_titular_divide2.btn_select_titular.clicked.connect(self.cerrar_select_titular_divide2)
        
        
        self.dlg_select_titular_divide2_buscar_nombre.btn_cancelar.clicked.connect(self.cerrar_select_titular_divide2_buscar_nombre)
        self.dlg_select_titular_divide2_buscar_nombre.btn_aceptar.clicked.connect(self.cerrar_select_titular_divide2_buscar_nombre)
        self.dlg_select_titular_divide2_buscar_nombre.btn_busca.clicked.connect(self.titular_divide2_busca_nombre)
        
        
        self.dlg_select_titular_divide2_buscar_ref.btn_cancelar.clicked.connect(self.cerrar_select_titular_divide1_buscar_ref)
        self.dlg_select_titular_divide2_buscar_ref.btn_aceptar.clicked.connect(self.cerrar_select_titular_divide1_buscar_ref)
        self.dlg_select_titular_divide2_buscar_ref.btn_busca.clicked.connect(self.titular_divide2_busca_ref)


        self.dlg_info_codigo_divide2.btn_guardar.clicked.connect(self.abrir_confirmar_divide)
        self.dlg_info_codigo_divide2.btn_guardar.clicked.connect(self.cerrar_dlg_info_codigo_divide2)
        self.dlg_info_codigo_divide2.btn_cancelar.clicked.connect(self.cerrar_dlg_info_codigo_divide2)


        
                   
        self.dlg_confirmar_divide.btn_guardar.clicked.connect(self.cerrar_confirmar_divide)
        self.dlg_confirmar_divide.btn_guardar.clicked.connect(self.divide_titular)




        # self.dlg_info_codigo_divide1
        # self.dlg_info_codigo_divide2
        
        
            # def abrir_dlg_info_codigo_divide2(self):
        # self.dlg_info_codigo_divide2.show()
 
    # def cerrar_dlg_info_codigo_divide2(self):
        # self.dlg_info_codigo_divide2.close() 



#################################################################################################################################################################
##############################################################FUNCIONES DE  ABRIR Y CERRAR DIALOGOS################################################################   
    
    def abrir_dialogo_titulares(self): 
        self.dlg_listar_titular.show() 
    def abrir_busqueda(self):
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dlg_busqueda)
        self.dlg_busqueda.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dlg_busqueda.show()
        self.dlg_busqueda.search()

    def abrir_ordenesTrabajo(self):
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dlg_ot)
        self.dlg_ot.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dlg_ot.show()
        self.dlg_ot.search()


    def cerrar_busqueda(self):
        self.dlg_busqueda.close()

    def abrir_dialogo_titular(self):
        self.dlg_export_titular.show()
        
    
    def abrir_dialogo_listar_titular(self):
        self.dlg_select_titular.show()
 
    def cerrar_dialogo_listar_titular(self):
        self.dlg_select_titular.close()
        



    def abrir_dialogo_listar_titular_buscar_ref(self):
        self.dlg_select_titular_busca_ref.show()
 
    def cerrar_dialogo_listar_titular_buscar_ref(self):
        self.dlg_select_titular_busca_ref.close()

    def abrir_dialogo_listar_titular_buscar_nombre(self):
        self.dlg_select_titular_busca_nombre.show()

    def cerrar_dialogo_listar_titular_buscar_nombre(self):
        self.dlg_select_titular_busca_nombre.close()




    def abrir_dialogo_listar_titular_feature(self):
        self.dlg_select_titular_feature.show()
 
    def cerrar_dialogo_listar_titular_feature(self):
        self.dlg_select_titular_feature.close()        
        
        
        
    def abrir_dialogo_cargacsv(self):
        self.dlg.show()
        
    def cerrar_dialogo_cargacsv(self):
        self.dlg.close()
        
        
        
                
    def abrir_dialogo_exportbbdd(self):
        self.dlg_export.show()
        
    def cerrar_dialogo_exportbbdd(self):
        self.dlg_export.close()
        
    
    def abrir_dialogo_exportartitular(self):
        self.dlg_export_titular.show()
        
    def cerrar_dialogo_exportartitular(self):
        self.dlg_export_titular.close()
        

    def abrir_dialogo_exportartitular_feature(self):
        self.dlg_export_titular_feature.show()
        
    def cerrar_dialogo_exportartitular_feature(self):
        self.dlg_export_titular_feature.close()
        
        
    def abrir_dialogo_listar_titular_feature_buscar_ref(self):
        self.dlg_select_titular_feature_busca_ref.show()
 
    def cerrar_dialogo_listar_titular_feature_buscar_ref(self):
        self.dlg_select_titular_feature_busca_ref.close()

    def abrir_dialogo_listar_titular_feature_buscar_nombre(self):
        self.dlg_select_titular_feature_busca_nombre.show()

    def cerrar_dialogo_listar_titular_feature_buscar_nombre(self):
        self.dlg_select_titular_feature_busca_nombre.close()
     
     
     

        
        
    #FUNCIONES DE DIALOGOS DE CONSTRUCCION
        
    def referenciar_construccion(self):
        try:
            # Obtener el layer activo y la feature seleccionada
            layer = iface.activeLayer()
            features = layer.selectedFeatures()
            
            if not features:
                self.driver.showMessage('Por favor seleccione una construcción', 1, 15)
                return
                
            feature = features[0]
            # Guardar el ID de la construcción seleccionada y el layer
            selected_construction_id = feature.id()
            construction_layer = layer  # Guardamos referencia al layer de construcciones

            list_widget = self.dlg_export_feature_construccion.list_bbdd
            current = list_widget.currentItem()
            if current:
                codigo = current.text().split()[0]
            else:
                campos = feature.fields().names()
                for campo in campos:
                    if 'cod' in campo.lower() or 'codigo' in campo.lower():
                        codigo = feature[campo]
                        break
                else:
                    self.driver.showMessage('No se pudo determinar el código catastral', 1, 15)
                    return
            
            # Configurar la conexión a la base de datos
            params = self.driver.params
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            
            # SQL para obtener el terreno específico
            sql = f"SELECT * FROM catastro.terrenos19 WHERE codigo = '{codigo}'"
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            
            # Crear una capa temporal con el terreno
            terreno_layer = QgsVectorLayer(uri.uri(False), 'terreno_temp', 'postgres')
            
            if not terreno_layer.isValid() or terreno_layer.featureCount() == 0:
                self.driver.showMessage('No se encontró el terreno correspondiente', 1, 15)
                return
            
            # Remover capas anteriores si existen
            layers = QgsProject.instance().mapLayersByName('terreno_temp')
            for old_layer in layers:
                QgsProject.instance().removeMapLayer(old_layer.id())
            
            # Agregar la nueva capa y aplicar estilo
            QgsProject.instance().addMapLayer(terreno_layer)    
            terreno_layer.loadNamedStyle(self.plugin_dir + r'\estilos\layer_terreno.qml')
            
            # Modificar el símbolo para que sea transparente con borde azul
            symbol = QgsFillSymbol.createSimple({
                'color': 'transparent',
                'outline_color': '#0000FF',
                'outline_width': '0.5',
                'outline_style': 'solid'
            })
            terreno_layer.renderer().setSymbol(symbol)
            
            # Mantener las configuraciones de etiqueta del QML pero cambiar el campo a mostrar
            label_settings = terreno_layer.labeling().settings()
            if label_settings:
                label_settings.fieldName = "codigo"  # Cambiar el campo a mostrar
                terreno_layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
                terreno_layer.setLabelsEnabled(True)
            
            terreno_layer.triggerRepaint()
            
            # Hacer zoom 
            canvas = iface.mapCanvas()
            canvas.setExtent(terreno_layer.extent())
            canvas.zoomScale(300)
            
            # Asegurarse de que el terreno temporal no tenga selección
            terreno_layer.removeSelection()
            
            # Volver a seleccionar solo la construcción original asegurándonos que el layer es el correcto
            if construction_layer and construction_layer.isValid():
                construction_layer.select(selected_construction_id)
                # Mostrar el formulario de la feature usando iface
                iface.openFeatureForm(construction_layer, feature)
            
            canvas.refresh()
            
            # Asegurarnos de que el layer activo sea el de construcciones
            iface.setActiveLayer(construction_layer)
            
            self.driver.showMessage('Terreno localizado exitosamente', 0, 3)
            
            return True
            
        except Exception as ex:
            print(f"Error en referenciar_construccion: {str(ex)}")
            self.driver.showMessage(f'Error al referenciar: {str(ex)}', 1, 15)
            return False
       
    
    def abrir_dialogo_guardarfeature_construccion(self):
        self.dlg_guardar_feature_construccion.show()
        iface.actionSelect().trigger()

    def cerrar_dialogo_guardarfeature_construccion(self):
        self.dlg_guardar_feature_construccion.close()
             
    
    def abrir_dialogo_exportbbdd_feature_construccion(self):
        self.dlg_export_feature_construccion.show()
        self.cargar_tablabbdd_construccion()  # Cargar los datos en el list widget
        
    def cerrar_dialogo_exportbbdd_feature_construccion(self):
        self.dlg_export_feature_construccion.close()
        
    
    def abrir_dialogo_export_plantas(self):
        self.dlg_export_plantas.show()
              
        
    def cerrar_dialogo_export_plantas(self):
        self.dlg_export_plantas.close() 
     
     
    def abrir_dialogo_layout(self):
        self.dlg_layout.show()
        
        self.cargar_tablabbdd()
               
        
    def cerrar_dialogo_layout(self):
        self.dlg_layout.close()
        
  



  
    def abrir_dialogo_informe(self):
        self.dlg_informe.show()
        self.cargar_tablabbdd2()
        
    def cerrar_dialogo_informe(self):
        self.dlg_informe.close()
               


    
    def abrir_dialogo_select_terreno_informe_busca_ref(self):
        self.dlg_select_terreno_informe_busca_ref.show()
    
    def cerrar_dialogo_select_terreno_informe_busca_ref(self):
        self.dlg_select_terreno_informe_busca_ref.close()


    def abrir_dialogo_select_terreno_informe_busca_nombre(self):
        self.dlg_select_terreno_informe_busca_nombre.show()
    
    def cerrar_dialogo_select_terreno_informe_busca_nombre(self):
        self.dlg_select_terreno_informe_busca_nombre.close()


     
    def abrir_dialogo_guardarfeature(self):
        self.dlg_guardar_feature.show()
        
        iface.actionSelect().trigger()


    def cerrar_dialogo_guardarfeature(self):
        self.dlg_guardar_feature.close()

    def abrir_dialogo_guardarManzanas(self): 
        self.dlg_guardar_manzanas.show() 



    def abrir_dialog_guardar_ejevias(self): 
        self.dlg_guardar_ejevia.show()
    
    def cerrar_dialog_guardar_ejevias(self): 
        self.dlg_guardar_ejevia.close()
    
    def abrir_dialogo_guardar_zonas(self):
        self.dlg_guardar_zona.show()

    def cerrar_dialog_guardar_zonas(self): 
        self.dlg_guardar_zona.close()
        
       
        
    
    def abrir_dialogo_exportbbdd_feature(self):
        #! CODIGO NUEVO YAPA 
        lyr = iface.activeLayer() 
        feat = lyr.selectedFeatures()[0]
        # print(feat['codigo'])
        try:
            self.dlg_export_feature.txt_referencia.setText(str(feat['codigo']))
            self.dlg_export_feature.txt_calle.setText(str(feat['direccion']))
            self.dlg_export_feature.txt_manzano.setText(str(feat['manzano']))
            self.dlg_export_feature.txt_predio.setText(str(feat['predio']))
            self.dlg_export_feature.txt_sub.setText(str(feat['subpredio']))
            self.dlg_export_feature.txt_zona.setText(str(feat['barrio']))
            self.dlg_export_feature.txt_suptest.setText('0')
            self.dlg_export_feature.txt_frente.setText(str(feat['frente']))
            self.dlg_export_feature.txt_fondo.setText(str(feat['fondo']))
        except Exception as ex:
            print(ex)
            pass
        self.dlg_export_feature.show()
        
    def cerrar_dialogo_exportbbdd_feature(self):
        self.dlg_export_feature.close()    
        
         
       
    def activa_seleccion(self):
        iface.actionSelect().trigger()
      
    def desactiva_seleccion(self):
        iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
        
    
    
    def abrir_dialogo_exportbbdd_especiales(self):
        self.dlg_export_especial.show()
        
    def cerrar_dialogo_exportbbdd_especiales(self):
        self.dlg_export_especial.close() 

    
    def abrir_dialogo_exportbbdd_mejoras(self):
        self.dlg_export_mejora.show()
        
    def cerrar_dialogo_exportbbdd_mejoras(self):
        self.dlg_export_mejora.close()    


    def abrir_dialogo_exportbbdd_plantas(self):
        self.dlg_export_planta.show()
        
    def cerrar_dialogo_exportbbdd_plantas(self):
        self.dlg_export_planta.close() 



#BOTON MATERIALES Y PLANTAS

    def limpiar_busqueda_plantas(self):
        """
        Método para limpiar la lista de construcciones y plantas
        """
        try:
            # Limpia la lista
            self.dlg_listar_construccion_plantas.list_bbdd.clear()
            
            # Opcional: Mostrar mensaje de éxito
            QMessageBox.information(None, "Éxito", "Búsqueda limpiada correctamente")
            
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error al limpiar la búsqueda: {str(e)}")
    
    def abrir_dialogo_exportbbdd_planta(self):
        """Abre el diálogo para exportar plantas a la base de datos"""
        try:
            # Verificar que el diálogo ListarConstruccionPlantas esté inicializado
            if not hasattr(self, 'dlg_listar_construccion_plantas'):
                self.driver.showMessage("Error al acceder al diálogo de construcciones", 1, 5)
                return
                
            # Obtener la construcción seleccionada desde ListarConstruccionPlantas
            construccion_id = self.dlg_listar_construccion_plantas.construccion_seleccionada
            construccion_data = self.dlg_listar_construccion_plantas.construccion_data
            
            if not construccion_id or not construccion_data:
                self.driver.showMessage("Primero debe seleccionar una construcción", 1, 5)
                return
                
            print(f"Abriendo diálogo para construcción ID: {construccion_id}")
            print(f"Datos de construcción: {construccion_data}")
            
            # Obtener datos completos y actualizados de la construcción
            sql = f"""
                SELECT c.id, c.numbloque, c.codigo, c.numplanta, c.antiguedad,
                    cv.superficie, cv.tipoconstruccion, cv.nombreuso
                FROM catastro.construcciones19 c
                JOIN catastro.construccionesvista19 cv ON c.id = cv.id
                WHERE c.id = {construccion_id};
            """
            datos_actualizados = self.driver.read(sql, multi=False)
            
            # Si no hay datos, usar los que ya tenemos
            if not datos_actualizados:
                datos_actualizados = construccion_data
                print("ADVERTENCIA: No se pudieron obtener datos actualizados de la construcción")
            
            # Determinar qué clase usar basado en la configuración y necesidades del proyecto
            # (Depende de cómo estén estructuradas tus clases)
            
            # Opción 1: Usar ExportPlantas
            self.dlg_export_planta = ExportPlantas(
                parent=self.iface.mainWindow(), 
                construccion_data=datos_actualizados
            )
            
            # Opción 2: Usar ExportDatabasePlantas (descomentar y usar según necesidad)
            # self.dlg_export_planta = ExportDatabasePlantas(
            #     parent=self.iface.mainWindow(),
            #     construccion_id=construccion_id,
            #     db_driver=self.driver
            # )
            
            # Evitamos llamar a cargar_plantas() directamente, ya que puede causar errores
            # La inicialización se debe hacer dentro del constructor de la clase
            
            # Conectar cualquier señal necesaria
            if hasattr(self.dlg_export_planta, 'btn_exportdb'):
                # Desconectar señales previas si es necesario
                try:
                    self.dlg_export_planta.btn_exportdb.clicked.disconnect()
                except:
                    pass
                    
                # Conectar señal a método apropiado si es necesario
                # self.dlg_export_planta.btn_exportdb.clicked.connect(self.algun_metodo)
            
            # Mostrar el diálogo de forma modal
            print("Mostrando diálogo de plantas...")
            resultado = self.dlg_export_planta.exec_()
            
            # Procesar el resultado
            if resultado == QDialog.Accepted:
                print("✅ Diálogo aceptado - Plantas guardadas correctamente")
                self.driver.showMessage("Plantas guardadas correctamente", 3, 5)
                
                # Actualizar cualquier información necesaria después de guardar
                if hasattr(self, 'dlg_listar_construccion_plantas'):
                    self.dlg_listar_construccion_plantas.cargar_construcciones()
                    print("Lista de construcciones actualizada")
            else:
                print("❌ Diálogo cancelado - No se guardaron cambios")
            
        except Exception as e:
            print(f"ERROR al abrir diálogo de plantas: {str(e)}")
            import traceback
            traceback.print_exc()
            self.driver.showMessage(f"Error: {str(e)}", 1, 5)
        
    def cerrar_dialogo_exportbbdd_planta(self):
        """Este método debe ser llamado desde el diálogo, no conectado directamente"""
        try:
            print("Cerrando diálogo de plantas")
            # Cualquier limpieza necesaria
        except Exception as e:
            print(f"Error al cerrar diálogo: {str(e)}") 
       

            
    def cerrar_dialogo_listarconstruccion_plantas(self):
        self.dlg_listar_construccion_plantas.close() 
        
        
    
    def abrir_dialogo_select_construccion_planta_busca_ref(self):    
        self.dlg_select_construccion_planta_busca_ref.show()
 
    def cerrar_dialogo_select_construccion_planta_busca_ref(self):    
        self.dlg_select_construccion_planta_busca_ref.close() 
        
    

#BOTON CERTIFICADO CATASTRAL


    def abrir_dialogo_informe2(self):
        self.dlg_informe2.show()
        self.cargar_tablabbdd3()
        
    def cerrar_dialogo_informe2(self):
        self.dlg_informe2.close()
        
    
    def abrir_select_terreno_layout_busca_ref(self):
        self.dlg_select_terreno_layout_busca_ref.show()
        
    def cerrar_select_terreno_layout_busca_ref(self):
        self.dlg_select_terreno_layout_busca_ref.close()
        
        
    def abrir_select_terreno_layout_busca_nombre(self):
        self.dlg_select_terreno_layout_busca_nombre.show()
        
    def cerrar_select_terreno_layout_busca_nombre(self):
        self.dlg_select_terreno_layout_busca_nombre.close()
    
        
    def abrir_dialogo_select_terreno_informe2_busca_ref(self):
        self.dlg_select_terreno_informe2_busca_ref.show()
    
    def cerrar_dialogo_select_terreno_informe2_busca_ref(self):
        self.dlg_select_terreno_informe2_busca_ref.close()


    def abrir_dialogo_select_terreno_informe2_busca_nombre(self):
        self.dlg_select_terreno_informe2_busca_nombre.show()
    
    def cerrar_dialogo_select_terreno_informe2_busca_nombre(self):
        self.dlg_select_terreno_informe2_busca_nombre.close()
            

#   BOTON CERTIFICADO AVALUO

    def abrir_dialogo_informe3(self):
        self.dlg_informe3.show()
        self.cargar_tablabbdd4()
    
    def cargar_tablabbdd4(self):
        """Carga la lista de terrenos para el informe 3"""
        try:
            list_widget = self.dlg_informe3.list_bbdd
            
            # Limpiar lista actual
            for i in range(list_widget.count()):
                list_widget.takeItem(0)
            
            # Consultar terrenos
            r = self.driver.read('select codigo, nombre, apellidos, documento from catastro.terrenosvista19')
            
            # Crear lista con formato: código + nombre + apellidos
            lista = []
            for item in r:
                if item["nombre"] or item["apellidos"]:
                    lista.append(str(item["codigo"]) + "   " + str(item["nombre"]) + "   " + str(item["apellidos"]))
                else:
                    lista.append(str(item["codigo"]))

            list_widget.addItems(lista)
            self.lista_terreno_informe3 = r

        except Exception as e:
            print(f"Error al cargar terrenos: {str(e)}")
            self.driver.showMessage("Error al cargar lista de terrenos", 2, 5)    
        
    def cerrar_dialogo_informe3(self):
        self.dlg_informe3.close() 
    
    def dlg_listar_construccion_plantas(self):
        self.dlg_listar_construccion.show()
        self.cargar_construccion()
        
    def dlg_listar_construccion_plantas(self):
        self.dlg_listar_construccion.close() 
    
    
    
    def abrir_dialogo_select_terreno_informe3_busca_ref(self):
        self.dlg_select_terreno_informe3_busca_ref.show()
    
    def cerrar_dialogo_select_terreno_informe3_busca_ref(self):
        self.dlg_select_terreno_informe3_busca_ref.close()


    def abrir_dialogo_select_terreno_informe3_busca_nombre(self):
        self.dlg_select_terreno_informe3_busca_nombre.show()
    
    def cerrar_dialogo_select_terreno_informe3_busca_nombre(self):
        self.dlg_select_terreno_informe3_busca_nombre.close()   
        
        
        
    # BOTON CAMBIAR TITULAR
    
    #abro y cierro  
    
    def abrir_dialogo_guardarfeature_cambiarTitular(self):
        self.dlg_guardar_feature_cambiar_titular.show()
        
        iface.actionSelect().trigger()


    def cerrar_dialogo_guardarfeature_cambiarTitular(self):
        self.dlg_guardar_feature_cambiar_titular.close()
        
        
        
    def abrir_select_titular_cambio_titular(self):
        self.dlg_select_titular_cambio_titular.show()
    

    def cerrar_select_titular_cambio_titular(self):
        self.dlg_select_titular_cambio_titular.close()    
        
        
        
    def abrir_select_titular_cambio_titular_busca_ref(self):    
       self.dlg_select_titular_cambio_titular_busca_ref.show()
       

    def cerrar_select_titular_cambio_titular_busca_ref(self):    
       self.dlg_select_titular_cambio_titular_busca_ref.close()      


    def abrir_select_titular_cambio_titular_busca_nombre(self):    
       self.dlg_select_titular_cambio_titular_busca_nombre.show()
       

    def cerrar_select_titular_cambio_titular_busca_nombre(self):    
       self.dlg_select_titular_cambio_titular_busca_nombre.close()         
       
       
       
    def abrir_confirmar_guardar_titular(self):
        self.confirmar_guardar_titular.show()
    
    
    def cerrar_confirmar_guardar_titular(self):
        self.confirmar_guardar_titular.close()
        
        
        
        
    ##################### UNION DE PARCELAS ##################################################################
    
    
    def abrir_guardar_feature_union(self):
        self.dlg_guardar_feature_union.show()
        iface.actionSelect().trigger()
        
    def cerrar_guardar_feature_union(self):
        self.dlg_guardar_feature_union.close()       
        
        
    def abrir_select_titular_union(self):
        self.dlg_select_titular_union.show()
 
    def cerrar_select_titular_union(self):
        self.dlg_select_titular_union.close() 
       
 
    def abrir_select_titular_union_busca_ref(self):
        self.dlg_select_titular_union_busca_ref.show()
 
    def cerrar_select_titular_union_busca_ref(self):
        self.dlg_select_titular_union_busca_ref.close()

        
    def abrir_select_titular_union_busca_nombre(self):
        self.dlg_select_titular_union_busca_nombre.show()
 
    def cerrar_select_titular_union_busca_nombre(self):
        self.dlg_select_titular_union_busca_nombre.close()  
  

    def abrir_confirmar_union(self):
        self.dlg_confirmar_union.show()
 
    def cerrar_confirmar_union(self):
        self.dlg_confirmar_union.close() 

    def abrir_dlg_info_codigo_union_union(self):
        self.dlg_info_codigo_union.show()
 
    def cerrar_dlg_info_codigo_union_union(self):
        self.dlg_info_codigo_union.close() 

     
    def abrir_info_forma_union(self):
        self.dlg_info_forma_union.show()
 
    def cerrar_info_forma_union(self):
        self.dlg_info_forma_union.close()   


    def abrir_info_inclinacion_union(self):
        self.dlg_info_inclinacion_union.show()
 
    def cerrar_info_inclinacion_union(self):
        self.dlg_info_inclinacion_union.close()         
  

    def abrir_material_calzada_union(self):
        self.dlg_info_material_calzada_union.show()
 
    def cerrar_material_calzada_union(self):
        self.dlg_info_material_calzada_union.close()  
  

    def abrir_tipo_calzada_union(self):
        self.dlg_info_tipo_calzada_union.show()
 
    def cerrar_tipo_calzada_union(self):
        self.dlg_info_tipo_calzada_union.close() 
        

    def abrir_dlg_info_ubicacion_union_union(self):
        self.dlg_info_ubicacion_union.show()
 
    def cerrar_dlg_info_ubicacion_union_union(self):
        self.dlg_info_ubicacion_union.close() 
        

    def abrir_dlg_info_zona_union_union(self):
        self.dlg_info_zona_union.show()
 
    def cerrar_dlg_info_zona_union_union(self):
        self.dlg_info_zona_union.close()         
        

    
    ##########################################DIVIDIR PARCELA############################################
    
    def abrir_guardar_feature_divide(self):
        self.dlg_guardar_feature_divide.show()
        iface.actionSelect().trigger()
        
    def cerrar_guardar_feature_divide(self):
        self.dlg_guardar_feature_divide.close()       
        
    
    def abrir_guardar_linea_divide(self):
        self.dlg_guardar_linea_divide.show()
        iface.actionSelect().trigger()
        
    def cerrar_guardar_linea_divide(self):
        self.dlg_guardar_linea_divide.close()

        
    def abrir_select_titular_divide1(self):
        self.dlg_select_titular_divide1.show()
        
    def cerrar_select_titular_divide1(self):
        self.dlg_select_titular_divide1.close()
        

    def abrir_select_titular_divide2(self):
        self.dlg_select_titular_divide2.show()
        
    def cerrar_select_titular_divide2(self):
        self.dlg_select_titular_divide2.close()        
        
        
    def abrir_select_titular_divide1_buscar_ref(self):
        self.dlg_select_titular_divide1_buscar_ref.show()
        
    def cerrar_select_titular_divide1_buscar_ref(self):
        self.dlg_select_titular_divide1_buscar_ref.close()        
 
 
    def abrir_select_titular_divide2_buscar_ref(self):
        self.dlg_select_titular_divide2_buscar_ref.show()
        
    def cerrar_select_titular_divide2_buscar_ref(self):
        self.dlg_select_titular_divide2_buscar_ref.close()          
        

    def abrir_select_titular_divide1_buscar_nombre(self):
        self.dlg_select_titular_divide1_buscar_nombre.show()
        
    def cerrar_select_titular_divide1_buscar_nombre(self):
        self.dlg_select_titular_divide1_buscar_nombre.close()        
 
 
    def abrir_select_titular_divide2_buscar_nombre(self):
        self.dlg_select_titular_divide2_buscar_nombre.show()
        
    def cerrar_select_titular_divide2_buscar_nombre(self):
        self.dlg_select_titular_divide2_buscar_nombre.close()   
 

    def abrir_confirmar_divide(self):
        self.dlg_confirmar_divide.show()
    
    def cerrar_confirmar_divide(self):
        self.dlg_confirmar_divide.close() 


    def abrir_dlg_info_codigo_divide1(self):
        self.dlg_info_codigo_divide1.show()
 
    def cerrar_dlg_info_codigo_divide1(self):
        self.dlg_info_codigo_divide1.close() 
    
 
    def abrir_dlg_info_codigo_divide2(self):
        self.dlg_info_codigo_divide2.show()
 
    def cerrar_dlg_info_codigo_divide2(self):
        self.dlg_info_codigo_divide2.close() 
        


    
    #######################################  FUNCIONES DE FUNCIONAMIENTO DE BOTONES #########################################################
    #########################################################################################################################################
    #########################################################################################################################################
    
    
    
    
    ############################################################################################################################################
    ############################################################BOTON GUARDA TITULAR##########################################################
    ############################################################################################################################################
    
    
    def guardar_titular(self):
        """
        Función para guardar titulares a la base de datos
        """        
        try:
            print("[App] Iniciando guardar_titular()")
            
            # Obtener valores de los campos
            valor_apellidos = self.dlg_export_titular.txt_apellidos.text().strip()
            valor_nombre = self.dlg_export_titular.txt_nombre.text().strip()
            valor_documento = self.dlg_export_titular.txt_documento.text().strip()
            
            print(f"[App] Datos obtenidos: Nombre='{valor_nombre}', Apellidos='{valor_apellidos}', Documento='{valor_documento}'")
            
            # Validar campos requeridos
            if not valor_apellidos or not valor_nombre or not valor_documento:
                self.driver.showMessage('Por favor complete todos los campos obligatorios', 1, 5)
                print("[App] Error: Campos incompletos")
                return False
            
            # Obtener índices de los combobox
            tipo_documento = self.dlg_export_titular.comboBox_tipo_prop.currentIndex()
            titularidad = self.dlg_export_titular.comboBox_titularidad_prop.currentIndex()
            documento_propiedad = self.dlg_export_titular.comboBox_doc_prop.currentIndex()
            adquisicion = self.dlg_export_titular.comboBox_adquisicion_prop.currentIndex()
            
            print(f"[App] Comboboxes: tipo_doc={tipo_documento}, titularidad={titularidad}, doc_prop={documento_propiedad}, adquisicion={adquisicion}")
            
            # Formatear los valores correctamente para SQL
            valor_apellidos = valor_apellidos.replace("'", "''")  # Escapar comillas simples
            valor_nombre = valor_nombre.replace("'", "''")
            valor_documento = valor_documento.replace("'", "''")

            # Construir la consulta SQL
            sql = f"""
            INSERT INTO catastro.titular 
                (nombre, apellidos, documento, tipo_doc, caracter, documento_prop, adquisicion)
            VALUES
                ('{valor_nombre}', '{valor_apellidos}', '{valor_documento}', 
                {tipo_documento}, {titularidad}, {documento_propiedad}, {adquisicion})
            """
            
            print(f"[App] SQL construido: {sql}")
            
            # Ejecutar la consulta usando el método create del driver
            resultado = self.driver.create(sql)
            print(f"[App] Resultado de create(): {resultado}")
            
            if resultado:
                # Limpiar los campos después de guardar exitosamente
                self.dlg_export_titular.txt_apellidos.clear()
                self.dlg_export_titular.txt_nombre.clear()
                self.dlg_export_titular.txt_documento.clear()
                
                self.dlg_export_titular.comboBox_tipo_prop.setCurrentIndex(0)
                self.dlg_export_titular.comboBox_titularidad_prop.setCurrentIndex(0)
                self.dlg_export_titular.comboBox_doc_prop.setCurrentIndex(0)
                self.dlg_export_titular.comboBox_adquisicion_prop.setCurrentIndex(0)
                
                print("[App] Campos limpiados después de guardar exitosamente")
                return True
            else:
                print("[App] Error: La función create() retornó False")
                return False
                
        except Exception as e:
            self.driver.showMessage(f'Error al guardar el titular: {str(e)}', 2, 5)
            print(f"[App] ERROR DETALLADO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    
    ############################################################################################################################################
    ############################################################BOTON CARGA ARCHIVO SHP o CSV###################################################
    ############################################################################################################################################
    
    titulares_cargados = ""
    
    
    def cargar_titular(self):
        """Carga la lista de titulares desde la tabla titular_old"""
        try: 
            sql = 'SELECT * FROM catastro.titular_old'
            r = self.driver.read(sql=sql)
            
            list_widget = self.dlg_select_titular.list_titular
            
            list_widget.clear()
            
            lista = []
                    
            for item in r:
                lista.append(f"{item['id']}    {item['nombre']} {item['apellidos']} {item['documento']}")

            list_widget.addItems(lista)
            
            self.titulares_cargar_titular_cargados = r  
        except Exception as ex: 
            print(f"Error al cargar titulares: {ex}")
            self.driver.showMessage(f"Error al cargar titulares: {ex}", 2, 5)  
       
            
    
    def titular_busca_ref(self):
        
        list_widget = self.dlg_select_titular.list_titular
        
        
        
        text_busqueda  = self.dlg_select_titular_busca_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText()
            
  
        try: 
            sql = f'''select * from catastro.titular where documento = '{valor_busqueda}' '''
            r = self.driver.read(sql=sql,multi=False)
            # print(r)
            if r != None:
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)

                item = str(r["id"]) + "    " + str(r["nombre"]) + " " + str(r["apellidos"]) + " " + str(r["documento"])
                list_widget.addItem(item)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex) 
    
    
                
    def titular_busca_nombre(self):
    
        list_widget = self.dlg_select_titular.list_titular
               
        text_busqueda  = self.dlg_select_titular_busca_nombre.text_titular
        valor_busqueda = text_busqueda.toPlainText().lower()
              
        try: 
            
            l = valor_busqueda.split()
            valor_busqueda = ''
            for e in l: 
                valor_busqueda  = valor_busqueda + '%' + e + '% '
            # print(valor_busqueda)
            sql = f''' select * from catastro.titular 
            where nombre || ' ' ||apellidos ilike '{valor_busqueda[:-1]}' '''
            r = self.driver.read(sql=sql)
            # print(r)
            
            if len(r) > 0 :
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                lista = []
                for item in r:
                    lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))
                
                list_widget.addItems(lista)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex)
        

        
    #CARGAR ARCHIVO
        
    def cargar_csv(self):
        """
        Carga archivos de tipo CSV o SHP para crear polígonos.
        
        El CSV debe contener:
        - Columna 'xcoord': Coordenada X en UTM
        - Columna 'ycoord': Coordenada Y en UTM
        - Delimitador: punto y coma (;)
        
        Returns:
            QgsVectorLayer: Capa vectorial con el polígono creado
            str: Mensaje de error en caso de fallo
        """
        try:
            # Obtener archivo seleccionado
            file_widget = self.dlg.carga_archivo
            file_src = file_widget.filePath()
            
            # Validar que se haya seleccionado un archivo
            if not file_src:
                self.driver.showMessage('No se ha seleccionado ningún archivo', 1, 15)
                return None
                
            file_src_end = file_src[-3:]
            
            # Procesar archivo SHP
            if file_src_end == 'shp':      
                vector_layer = QgsVectorLayer(file_src, 'poligono_shp', 'ogr')
                
                if not vector_layer.isValid():
                    self.driver.showMessage('Error al cargar el archivo shapefile', 1, 15)
                    return None
                    
            # Procesar archivo CSV
            elif file_src_end == 'csv':
                # Configurar diferentes delimitadores para probar
                delimiters = [';', ',', '\t']
                vector_layer = None
                
                for delimiter in delimiters:
                    uri = f'file:///{file_src}?delimiter={delimiter}&yField=ycoord&xField=xcoord'
                    temp_layer = QgsVectorLayer(uri, 'temp_csv', 'delimitedtext')
                    
                    if temp_layer.isValid() and temp_layer.featureCount() > 0:
                        vector_layer = temp_layer
                        break
                
                if not vector_layer or not vector_layer.isValid():
                    self.driver.showMessage('Error al cargar el CSV. Verifique el formato y delimitador', 1, 15)
                    return None
                    
                features_puntuales = list(vector_layer.getFeatures())
                
                # Verificar número mínimo de puntos
                if len(features_puntuales) < 3:
                    self.driver.showMessage('Se necesitan al menos 3 puntos para crear un polígono', 1, 15)
                    return None
                    
                lista_puntos = []
                
                # Procesar coordenadas
                try:
                    for f in features_puntuales:
                        point_x = float(f["xcoord"])
                        point_y = float(f["ycoord"])
                        
                        # Validar coordenadas
                        if point_x == 0 or point_y == 0:
                            self.driver.showMessage('Coordenadas inválidas encontradas', 1, 15)
                            return None
                            
                        point = QgsPointXY(point_x, point_y)
                        lista_puntos.append(point)
                        
                    # Cerrar el polígono añadiendo el primer punto
                    lista_puntos.append(lista_puntos[0])
                    
                except (ValueError, KeyError) as e:
                    self.driver.showMessage(f'Error en el formato de coordenadas: {str(e)}', 1, 15)
                    return None
                    
                # Crear feature con el polígono
                nueva_feature = QgsFeature()
                nueva_feature.setGeometry(QgsGeometry.fromPolygonXY([lista_puntos]))
                
                # Crear capa vectorial
                vector_layer = QgsVectorLayer("MULTIPOLYGON?crs=EPSG:32719", "poligono_csv", "memory")
                
                if not vector_layer.isValid():
                    self.driver.showMessage('Error al crear la capa vectorial', 1, 15)
                    return None
                    
                vector_layer.dataProvider().addFeatures([nueva_feature])
                
            else:
                self.driver.showMessage('Formato de archivo no soportado. Use CSV o SHP', 1, 15)
                return None
                
            # Obtener geometría del polígono creado
            features_del_archivo = list(vector_layer.getFeatures())
            if not features_del_archivo:
                self.driver.showMessage('No se pudieron crear geometrías', 1, 15)
                return None
                
            feature_uno = features_del_archivo[0]
            geometria_del_archivo = feature_uno.geometry()
            
            if not geometria_del_archivo:
                self.driver.showMessage('Error al obtener la geometría', 1, 15)
                return None
                
            geometriaWkt = geometria_del_archivo.asWkt()
            srid = vector_layer.crs().authid()[5:]
            
            # Extraer puntos para exportar
            listPointsToExport = []
            try:
                for listPointsGeometry in geometria_del_archivo.asPolygon():
                    for listPoints in listPointsGeometry:
                        listPointsToExport.append([listPoints.x(), listPoints.y()])
                        
                return vector_layer, geometriaWkt, srid, listPointsToExport
                
            except Exception as e:
                self.driver.showMessage(f'Error al procesar la geometría: {str(e)}', 1, 15)
                return None
                
        except Exception as e:
            self.driver.showMessage(f'Error general: {str(e)}', 1, 15)
            return None
                    
        
        features_del_archivo = list(vector_layer.getFeatures())
        feture_uno = features_del_archivo[0]
        
        geometria_del_archivo = feture_uno.geometry()
        geometriaWkt = features_del_archivo[0].geometry().asWkt() #! PENDIENTE TEST
        # print(geometria)
        srid = vector_layer.crs().authid()[5:] #! PENDIENTE TEST
 
  
        
        listPointsToExport = []
        
        for listPointsGeometry in geometria_del_archivo.asPolygon():
            for listPoints in listPointsGeometry:
                listPointsToExport.append([listPoints.x(), listPoints.y()])

        
        print(listPointsToExport)

        
        
        list_widget = self.dlg_select_titular.list_titular
        current = list_widget.currentItem()
        
        
        #Obtengo el texto del QListWidgetItem
        list_widget_name = current.text()
        
        titular_tuple = list_widget_name.split()
        
 
        
        #Añado datos a los campos que se crean en el plugin y paso la feature llena
        text_codigo = self.dlg_export.txt_referencia
        valor_codigo = text_codigo.toPlainText()
        
        text_direccion = self.dlg_export.txt_calle
        valor_direccion = text_direccion.toPlainText()

        text_manzano = self.dlg_export.txt_manzano
        valor_manzano = text_manzano.toPlainText()
        
        text_predio = self.dlg_export.txt_predio 
        valor_predio  = text_predio.toPlainText()
        
        text_subpredio = self.dlg_export.txt_sub
        valor_subpredio = text_subpredio.toPlainText()       
        
        text_zona = self.dlg_export.txt_zona
        valor_zona = text_zona.toPlainText()
        

        text_suptest = self.dlg_export.txt_suptest
        valor_suptest = text_suptest.toPlainText()       

        
        
        text_frente = self.dlg_export.txt_frente
        valor_frente = text_frente.toPlainText()       
                
        text_fondo = self.dlg_export.txt_fondo
        valor_fondo = text_fondo.toPlainText()
        
        

        agua = self.dlg_export.checkBox_agua.isChecked()
        telefono = self.dlg_export.checkBox_telefono.isChecked()
        alcantarillado = self.dlg_export.checkBox_alcantarilla.isChecked()
        energia = self.dlg_export.checkBox_energia.isChecked()
        internet = self.dlg_export.checkBox_internet.isChecked()
        transporte = self.dlg_export.checkBox_transporte.isChecked()        
        
        
        
        text_norte = "norte"        
        text_sur = "sur" 
        text_este = "este"
        text_oeste = "oeste"

        
        
        text_base = self.dlg_export.txt_base
        valor_base = text_base.toPlainText()
        
        
        zona = self.dlg_export.comboBox_zona.currentIndex()
        material_via = self.dlg_export.comboBox_calzada.currentIndex()
        inclinacion = self.dlg_export.comboBox_inclinacion.currentIndex()
        ubicacion = self.dlg_export.comboBox_ubicacion.currentIndex()
        calzada = self.dlg_export.comboBox_tipocalzada.currentIndex()
        forma = self.dlg_export.comboBox_forma.currentIndex()
        

        cur_area = (geometria_del_archivo.area())
        
 
        
        #######################################añadir el id del titular ####################################
        titular = titular_tuple[0]
        
        

 
  
    
        # urlTerrenos19 = "http://192.168.0.150:8080/apiCatastro/terrenos19"
                
        # datos = {'codigo': valor_codigo, 'agua': agua, 'alcantarillado': alcantarillado, 'barrio': valor_zona, 'base': valor_base, 'direccion': valor_direccion, 
        # 'energia': energia, 'este': " ", 'fondo': valor_fondo, 'frente': valor_frente, 'internet': internet, 'manzano': valor_manzano, 'norte': " ", 'oeste': " ", 
        # 'predio': valor_predio, 'subpredio': valor_subpredio, 'superficie': cur_area, 'suptest': valor_suptest, 'sur': " ",  'telefono': telefono,  'transporte': transporte,
        # 'formaBean': {'id': forma}, 'materialViaBean': {'id': material_via}, 'tipoVia': {'id': calzada}, 'titularBean': {'id': titular}, 'topografiaBean': {'id': inclinacion}, 
        # 'ubicacionBean': {'id': ubicacion}, 'zonaBean': {'id': zona}, "geom": {"type": "MultiPolygon","coordinates": [[listPointsToExport]]}}
        
        
        # response = requests.post(urlTerrenos19, json=datos)
        
        # print(response.status_code)
        
        # if response.status_code == 201:
        #     print(response.content)
        #     QMessageBox.information(iface.mainWindow(), "Base de Datos", 'Información Guardada en la Base de Datos Correctamente')
        # else:
        #     QMessageBox.information(iface.mainWindow(), "Base de Datos", 'No se pude cargar la información en la Base de Datos')
        

        # sql = 

         #* CODIGO NUEVO
        sql = f'''  INSERT INTO catastro.terrenos19
        (codigo, direccion, superficie, barrio, via, agua, alcantarillado, energia, telefono, transporte, internet, titular, topografia, forma, ubicacion, frente, fondo, suptest, manzano, predio, subpredio, norte, sur, este, oeste, base, zona, material_via, geom)
        VALUES('{valor_codigo}', '{valor_direccion}', {cur_area}, '{valor_zona}', {calzada}, {agua}, {alcantarillado}, {energia}, {telefono}, {transporte}, {internet}, {titular}, {inclinacion}, {forma}, {ubicacion}, '{valor_frente}', '{valor_fondo}', '{valor_suptest}', '{valor_manzano}', '{valor_predio}', '{valor_subpredio}', '', '', '', '', '{valor_base}', {zona}, {material_via}, st_multi(st_force2d(st_transform(st_geomfromtext('{geometriaWkt}',{srid}),32719))))
        '''
        self.driver.create(sql) #* PASO TEST
        
        self.dlg_export.txt_referencia.clear()
        self.dlg_export.txt_calle.clear()
        self.dlg_export.txt_manzano.clear()
        self.dlg_export.txt_predio.clear() 
        self.dlg_export.txt_sub.clear()
        self.dlg_export.txt_zona.clear()
        self.dlg_export.txt_suptest.clear()
        self.dlg_export.txt_frente.clear()        
        self.dlg_export.txt_fondo.clear()
        
        self.dlg_export.checkBox_agua.setChecked(False)
        self.dlg_export.checkBox_telefono.setChecked(False)
        self.dlg_export.checkBox_alcantarilla.setChecked(False)
        self.dlg_export.checkBox_energia.setChecked(False)
        self.dlg_export.checkBox_internet.setChecked(False)
        self.dlg_export.checkBox_transporte.setChecked(False)
        
        self.dlg_export.txt_base.clear() 
        
        self.dlg_export.comboBox_zona.setCurrentIndex(0)
        self.dlg_export.comboBox_calzada.setCurrentIndex(0)
        self.dlg_export.comboBox_inclinacion.setCurrentIndex(0)
        self.dlg_export.comboBox_ubicacion.setCurrentIndex(0) 
        self.dlg_export.comboBox_tipocalzada.setCurrentIndex(0)
        self.dlg_export.comboBox_forma.setCurrentIndex(0)

 
    
    
     
    
    ############################################################################################################################################
    ######################################################### BOTON SELECCIONA POLIGONO ######################################################
    ############################################################################################################################################
    
                    
  
    titulares_feature_cargados = ""
   
    def cargar_titular_feature(self):
         
        list_widget = self.dlg_select_titular_feature.list_titular
        
        try: 
            sql = 'select * from catastro.titular'
            r = self.driver.read(sql=sql)
        except Exception as ex: 
            print(ex) 
    
        for i in range(list_widget.count()):
        
            list_widget.takeItem(0)
        
        lista = []
                
        for item in r:
            lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))

        # print(lista)
        list_widget.addItems(lista)
        
        self.titulares_cargar_titular_cargados = r  


        
       
    
 
    def titular_feature_busca_ref(self):
        
        list_widget = self.dlg_select_titular_feature.list_titular        
        text_busqueda  = self.dlg_select_titular_feature_busca_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText()
        # print(valor_busqueda)
            


        try: 
            sql = f'''select * from catastro.titular where documento = '{valor_busqueda}' '''
            r = self.driver.read(sql=sql,multi=False)
            # print(r)
            if r != None:
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)

                item = str(r["id"]) + "    " + str(r["nombre"]) + " " + str(r["apellidos"]) + " " + str(r["documento"])
                list_widget.addItem(item)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex) 
        
        
       
    def titular_feature_busca_nombre(self):
    
        list_widget = self.dlg_select_titular_feature.list_titular
        
           
        text_busqueda  = self.dlg_select_titular_feature_busca_nombre.text_titular
        valor_busqueda = text_busqueda.toPlainText().lower()

        try: 
            
            
            l = valor_busqueda.split()
            valor_busqueda = ''
            for e in l: 
                valor_busqueda  = valor_busqueda + '%' + e + '% '
            print(valor_busqueda)
            sql = f''' select * from catastro.titular 
            where nombre || ' ' ||apellidos ilike '{valor_busqueda[:-1]}' '''
            r = self.driver.read(sql=sql)
            # print(r)
            
            if len(r) > 0 :
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                lista = []
                for item in r:
                    lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))
                
                list_widget.addItems(lista)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex)
              
        
        
        
        
        
    
    def selecciona_feature(self):    
        
        layer = iface.activeLayer()
        
        features = layer.selectedFeatures()
        
        geometria = features[0].geometry()
        geometriaWkt = features[0].geometry().asWkt()
        # print(geometria)
        srid = layer.crs().authid()[5:]
        # print(srid)
        
                               
        n = 0
        ver = geometria.vertexAt(0)
        puntos = []
        
        while(ver.isEmpty() != True):
            ver = geometria.vertexAt(n)
            n +=1
            ver_xy = QgsPointXY(ver)
            puntos.append(ver_xy)
        
        puntos.pop()
        
        
        listPointsToExport = []
        
        for point in puntos:
            listPointsToExport.append([point.x(), point.y()])
        
        # print(listPointsToExport)
    
        
        
        list_widget = self.dlg_select_titular_feature.list_titular
        current = list_widget.currentItem()
        
        
        #Obtengo el texto del QListWidgetItem
        list_widget_name = current.text()
        
        titular_tuple = list_widget_name.split()
        
        
    #Añado datos a los campos que se crean en el plugin y paso la feature llena
        text_codigo = self.dlg_export_feature.txt_referencia
        valor_codigo = text_codigo.text()
        
        text_direccion = self.dlg_export_feature.txt_calle
        valor_direccion = text_direccion.text()

        text_manzano = self.dlg_export_feature.txt_manzano
        valor_manzano = text_manzano.text()
        
        text_predio = self.dlg_export_feature.txt_predio 
        valor_predio  = text_predio.text()
        
        text_subpredio = self.dlg_export_feature.txt_sub
        valor_subpredio = text_subpredio.text()       
        
        text_zona = self.dlg_export_feature.txt_zona
        valor_zona = text_zona.text()
        

        text_suptest = self.dlg_export_feature.txt_suptest
        valor_suptest = text_suptest.text()       

        
        text_frente = self.dlg_export_feature.txt_frente
        valor_frente = text_frente.text()       
                
        text_fondo = self.dlg_export_feature.txt_fondo
        valor_fondo = text_fondo.text()

        valor_n_test = self.dlg_export_feature.txt_ntest.text()
        valor_date_test = self.dlg_export_feature.date_test.date().toString("dd/MM/yyyy")
        valor_folio_rrdd = self.dlg_export_feature.txt_folioddrr.text()

        # print(valor_n_test,valor_date_test,valor_folio_rrdd)

        #! HASTA AQUI
        
        
        agua = self.dlg_export_feature.checkBox_agua.isChecked()
        telefono = self.dlg_export_feature.checkBox_telefono.isChecked()
        alcantarillado = self.dlg_export_feature.checkBox_alcantarilla.isChecked()
        energia = self.dlg_export_feature.checkBox_energia.isChecked()
        internet = self.dlg_export_feature.checkBox_internet.isChecked()
        transporte = self.dlg_export_feature.checkBox_transporte.isChecked()        
        
        
        text_norte = "norte"        
        text_sur = "sur"         
        text_este = "este"
        text_oeste = "oeste"
 
        
        text_base = self.dlg_export_feature.txt_base
        valor_base = text_base.text()
        
        
        zona = self.dlg_export_feature.comboBox_zona.currentIndex()
        material_via = self.dlg_export_feature.comboBox_calzada.currentIndex()
        inclinacion = self.dlg_export_feature.comboBox_inclinacion.currentIndex()
        ubicacion = self.dlg_export_feature.comboBox_ubicacion.currentIndex()
        calzada = self.dlg_export_feature.comboBox_tipocalzada.currentIndex()
        forma = self.dlg_export_feature.comboBox_forma.currentIndex()
        

        cur_area = (geometria.area())
        
        #######################################añadir el id del titular ####################################
        titular = titular_tuple[-1]
        
        
        #urlTerrenos19 = "http://192.168.0.150:8080/apiCatastro/terrenos19"
                
        datos = {'codigo': valor_codigo, 'agua': agua, 'alcantarillado': alcantarillado, 'barrio': valor_zona, 'base': valor_base, 'direccion': valor_direccion, 
        'energia': energia, 'este': " ", 'fondo': valor_fondo, 'frente': valor_frente, 'internet': internet, 'manzano': valor_manzano, 'norte': " ", 'oeste': " ", 
        'predio': valor_predio, 'subpredio': valor_subpredio, 'superficie': cur_area, 'suptest': valor_suptest, 'sur': " ",  'telefono': telefono,  'transporte': transporte,
        'formaBean': {'id': forma}, 'materialViaBean': {'id': material_via}, 'tipoVia': {'id': calzada}, 'titularBean': {'id': titular}, 'topografiaBean': {'id': inclinacion}, 
        'ubicacionBean': {'id': ubicacion}, 'zonaBean': {'id': zona}, "geom": {"type": "MultiPolygon","coordinates": [[listPointsToExport]]}}
        
        sql = f'''  INSERT INTO catastro.terrenos19
        (codigo, direccion, superficie, barrio, via, agua, alcantarillado, energia, telefono, transporte, internet, titular, topografia, forma, ubicacion, frente, fondo, suptest, manzano, predio, subpredio, norte, sur, este, oeste, base, zona, material_via, geom, n_test, fecha_test,folio_ddrr)
        VALUES('{valor_codigo}', '{valor_direccion}', {cur_area}, '{valor_zona}', {calzada}, {agua}, {alcantarillado}, {energia}, {telefono}, {transporte}, {internet}, {titular}, {inclinacion}, {forma}, {ubicacion}, '{valor_frente}', '{valor_fondo}', '{valor_suptest}', '{valor_manzano}', '{valor_predio}', '{valor_subpredio}', '', '', '', '', '{valor_base}', {zona}, {material_via}, st_multi(st_force2d(st_transform(st_geomfromtext('{geometriaWkt}',{srid}),32719))), '{valor_n_test}','{valor_date_test}','{valor_folio_rrdd}');
        '''

        # print(sql)

        self.driver.create(sql=sql)

        
        # , "geom": {"type": "MultiPolygon","coordinates": [[listPointsToExport]]}
        
        
        # response = requests.post(urlTerrenos19, json=datos)
        
        
        # if response.status_code == 201:
        #     print(response.content)
        #     QMessageBox.information(iface.mainWindow(), "Base de Datos", 'Información Guardada en la Base de Datos Correctamente')
        # else:
        #     QMessageBox.information(iface.mainWindow(), "Base de Datos", 'No se pude cargar la información en la Base de Datos')
          
        
        self.dlg_export_feature.txt_referencia.clear()
        self.dlg_export_feature.txt_calle.clear()
        self.dlg_export_feature.txt_manzano.clear()
        self.dlg_export_feature.txt_predio.clear() 
        self.dlg_export_feature.txt_sub.clear()
        self.dlg_export_feature.txt_zona.clear()
        self.dlg_export_feature.txt_suptest.clear()
        self.dlg_export_feature.txt_frente.clear()        
        self.dlg_export_feature.txt_fondo.clear()
        self.dlg_export_feature.txt_ntest.clear()
        self.dlg_export_feature.txt_folioddrr.clear()
        
        self.dlg_export_feature.checkBox_agua.setChecked(False)
        self.dlg_export_feature.checkBox_telefono.setChecked(False)
        self.dlg_export_feature.checkBox_alcantarilla.setChecked(False)
        self.dlg_export_feature.checkBox_energia.setChecked(False)
        self.dlg_export_feature.checkBox_internet.setChecked(False)
        self.dlg_export_feature.checkBox_transporte.setChecked(False)
        
        self.dlg_export.txt_base.clear() 
        
        self.dlg_export_feature.comboBox_zona.setCurrentIndex(0)
        self.dlg_export_feature.comboBox_calzada.setCurrentIndex(0)
        self.dlg_export_feature.comboBox_inclinacion.setCurrentIndex(0)
        self.dlg_export_feature.comboBox_ubicacion.setCurrentIndex(0)
        self.dlg_export_feature.comboBox_tipocalzada.setCurrentIndex(0)
        self.dlg_export_feature.comboBox_forma.setCurrentIndex(0)




    ############################################################################################################################################
    ############################################################TERCER BOTON SELECCIONA CONSTRUCCION##########################################################
    ############################################################################################################################################   


    def setup_search():
        # Conectar el evento textChanged del QLineEdit con la función de filtrado
        self.searchBox.textChanged.connect(self.filter_list)

    def filter_list(self, text):
        # Ocultar todos los items
        for i in range(self.list_bbdd.count()):
            item = self.list_bbdd.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    #Selecciona Construccion
    
    def selecciona_construccion(self):    
        try:
            # Verificar si hay una capa activa
            layer = iface.activeLayer()
            if not layer:
                self.driver.showMessage('No hay una capa activa', 1, 15)
                return
                
            # Verificar si hay features seleccionadas
            features = layer.selectedFeatures()
            if not features:
                self.driver.showMessage('Por favor seleccione una construcción', 1, 15)
                return
            
            # Obtener la geometría
            geometria = features[0].geometry()
            geometriaWkt = features[0].geometry().asWkt()
            srid = layer.crs().authid()[5:]
                    
            # Obtener los puntos de la geometría
            n = 0
            ver = geometria.vertexAt(0)
            puntos = []
            
            while(ver.isEmpty() != True):
                ver = geometria.vertexAt(n)
                n += 1
                ver_xy = QgsPointXY(ver)
                puntos.append(ver_xy)
            
            puntos.pop()
            
            listPointsToExport = []
            for point in puntos:
                listPointsToExport.append([point.x(), point.y()])
            
            # Verificar la selección en la lista
            list_widget = self.dlg_export_feature_construccion.list_bbdd
            current = list_widget.currentItem()
            if not current:
                self.driver.showMessage('Por favor seleccione un elemento de la lista', 1, 15)
                return
            
            # Obtener y verificar los valores de los campos
            cod = self.dlg_export_feature_construccion.cod
            valor_cod = cod.toPlainText()
            if not valor_cod:
                self.driver.showMessage('El campo código es obligatorio', 1, 15)
                return
            
            currentText = current.text()
            currentTextSplit = currentText.split()
            if not currentTextSplit:
                self.driver.showMessage('El texto seleccionado no tiene el formato esperado', 1, 15)
                return
                
            currentTextSplitCodigo = currentTextSplit[0]
            
            # Calcular área
            cur_area = features[0].geometry().area()
            
            # Obtener valores de los campos
            anyo = self.dlg_export_feature_construccion.anyo
            valor_anyo = anyo.toPlainText() or '0'  # Valor por defecto si está vacío
            
            plantas = self.dlg_export_feature_construccion.plantas
            valor_plantas = plantas.toPlainText() or '0'
            
            dorm = self.dlg_export_feature_construccion.dormitorios
            valor_dorm = dorm.toPlainText() or '0'
            
            banyos = self.dlg_export_feature_construccion.banyos
            valor_banyos = banyos.toPlainText() or '0'
            
            # Obtener índices de los combobox
            conservacion = self.dlg_export_feature_construccion.comboBox_conservacion.currentIndex()           
            uso = self.dlg_export_feature_construccion.comboBox_uso.currentIndex()
            tipo = self.dlg_export_feature_construccion.comboBox_tipo.currentIndex()       
            revestimiento = self.dlg_export_feature_construccion.comboBox_revestimiento.currentIndex()
            
            # Obtener estados de los checkboxes
            ascensor = self.dlg_export_feature_construccion.checkBox_ascensor.isChecked()
            calefaccion = self.dlg_export_feature_construccion.checkBox_calefaccion.isChecked()
            sanitarios = self.dlg_export_feature_construccion.checkBox_sanitarios.isChecked()
            escalera = self.dlg_export_feature_construccion.checkBox_escalera.isChecked()
            aire = self.dlg_export_feature_construccion.checkBox_aire.isChecked()
            lavanderia = self.dlg_export_feature_construccion.checkBox_lavandera.isChecked()
            agua = self.dlg_export_feature_construccion.checkBox_agua.isChecked()
            area = self.dlg_export_feature_construccion.checkBox_area.isChecked()
            
            # MODIFICACIÓN: Generar un ID único para la construcción
            # Consultar el último ID usado y sumar 1
            sql_ultimo_id = "SELECT MAX(id) AS ultimo_id FROM catastro.construcciones19"
            resultado_ultimo_id = self.driver.read(sql=sql_ultimo_id, multi=False)
            
            ultimo_id = 1  # Valor por defecto
            if resultado_ultimo_id:
                if isinstance(resultado_ultimo_id, dict) and 'ultimo_id' in resultado_ultimo_id:
                    ultimo_id = resultado_ultimo_id['ultimo_id'] + 1
                elif hasattr(resultado_ultimo_id, 'ultimo_id'):
                    ultimo_id = resultado_ultimo_id.ultimo_id + 1
                elif isinstance(resultado_ultimo_id, (list, tuple)) and resultado_ultimo_id[0] is not None:
                    ultimo_id = int(resultado_ultimo_id[0]) + 1
                else:
                    # Intentar acceder como si fuera un objeto con índice
                    try:
                        valor = resultado_ultimo_id[0]
                        if valor is not None:
                            ultimo_id = int(valor) + 1
                    except:
                        ultimo_id = 1
            
            print(f"Usando nuevo ID para construcción: {ultimo_id}")
            
            # Guardar el ID de la construcción como atributo de la clase
            self.ultimo_construccion_id = ultimo_id
            
            # Construir y ejecutar SQL con ID explícito
            sql = f''' INSERT INTO catastro.construcciones19
            (id, numbloque, codigo, plantas, anyo, estadoconservacion, uso, superficie, dormitorios, banyos, revestimiento, ascensores, calefaccion, aire, escalera, tanque, lavanderia, servicio, sanitarios, tipoconstruccion, geom)
            VALUES({ultimo_id}, {valor_cod}, '{currentTextSplitCodigo}', {valor_plantas}, '{valor_anyo}', {conservacion}, {uso}, {cur_area}, {valor_dorm}, {valor_banyos}, {revestimiento}, {ascensor}, {calefaccion}, {aire}, {escalera}, {agua}, {lavanderia}, {area}, {sanitarios}, {tipo}, st_multi(st_force2d(st_transform(st_geomfromtext('{geometriaWkt}',{srid}),32719))));
            '''

            self.driver.create(sql=sql)
            print(f"Construcción guardada con ID: {ultimo_id}")
            
            # Limpiar campos después de la inserción exitosa
            self.dlg_export_feature_construccion.cod.clear()
            self.dlg_export_feature_construccion.anyo.clear()      
            self.dlg_export_feature_construccion.plantas.clear()       
            self.dlg_export_feature_construccion.dormitorios.clear()
            self.dlg_export_feature_construccion.banyos.clear()           
            
            # Resetear comboboxes
            self.dlg_export_feature_construccion.comboBox_conservacion.setCurrentIndex(0)        
            self.dlg_export_feature_construccion.comboBox_uso.setCurrentIndex(0)
            self.dlg_export_feature_construccion.comboBox_tipo.setCurrentIndex(0)   
            self.dlg_export_feature_construccion.comboBox_revestimiento.setCurrentIndex(0)
            
            # Desmarcar checkboxes
            self.dlg_export_feature_construccion.checkBox_ascensor.setChecked(False)
            self.dlg_export_feature_construccion.checkBox_calefaccion.setChecked(False)
            self.dlg_export_feature_construccion.checkBox_sanitarios.setChecked(False)
            self.dlg_export_feature_construccion.checkBox_escalera.setChecked(False)
            self.dlg_export_feature_construccion.checkBox_aire.setChecked(False)
            self.dlg_export_feature_construccion.checkBox_lavandera.setChecked(False)
            self.dlg_export_feature_construccion.checkBox_agua.setChecked(False)
            self.dlg_export_feature_construccion.checkBox_area.setChecked(False)
            
            self.driver.showMessage('Construcción guardada exitosamente', 0, 3)
            
            # Crear plantas automáticamente
            self.crear_plantas_construccion(ultimo_id, valor_plantas, valor_anyo, cur_area)
            
            # NUEVO: Cerrar el diálogo actual y abrir DialogoConstruccion con el ID
            self.dlg_export_feature_construccion.close()
            self.abrir_dialogo_construccion(ultimo_id)
            
        except Exception as ex:
            print(f"Error en selecciona_construccion: {str(ex)}")
            self.driver.showMessage(f'Error al seleccionar: {str(ex)}', 1, 15)


    def abrir_dialogo_construccion(self, construccion_id):
        """
        Abre el diálogo DialogoConstruccion para modificar una construcción existente
        y gestionar sus plantas.
        
        Args:
            construccion_id (int): ID de la construcción a modificar.
        """
        try:
            # Importar la clase DialogoConstruccion si no está disponible
            # Esto permite mantener la separación de código
            if not hasattr(self, 'DialogoConstruccion'):
                from .dialogo_construccion import DialogoConstruccion
            
            # Crear una instancia del diálogo pasando el ID de la construcción
            dialogo = DialogoConstruccion(iface=self.iface, parent=self.iface.mainWindow(), construccion_id=construccion_id)
            
            # Mostrar el diálogo como modal
            dialogo.exec_()
            
            # Opcionalmente, se podría refrescar la capa de construcciones después de cerrar el diálogo
            self.refrescar_capa_construcciones()
            
        except Exception as ex:
            print(f"Error al abrir diálogo de construcción: {str(ex)}")
            self.driver.showMessage(f'Error al abrir diálogo de construcción: {str(ex)}', 1, 15)
            import traceback
            traceback.print_exc()


    def refrescar_capa_construcciones(self):
        """
        Refresca la capa de construcciones para mostrar los cambios realizados.
        """
        try:
            # Buscar la capa de construcciones en el proyecto
            for layer in QgsProject.instance().mapLayers().values():
                if 'construcciones19' in layer.name().lower():
                    # Refrescar la capa
                    layer.triggerRepaint()
                    print(f"Capa {layer.name()} refrescada")
                    break
        except Exception as ex:
            print(f"Error al refrescar capa: {str(ex)}")


    def crear_plantas_construccion(self, construccion_id, valor_plantas, valor_anyo, cur_area):
        """
        Función auxiliar para crear plantas de una construcción automáticamente.
        
        Args:
            construccion_id (int): ID de la construcción.
            valor_plantas (str): Número de plantas como string.
            valor_anyo (str): Año de construcción.
            cur_area (float): Superficie de la construcción.
        """
        try:
            if construccion_id:
                # Convertir número de plantas a entero
                num_plantas = int(valor_plantas) if valor_plantas.isdigit() else 0
                plantas_creadas = 0
                
                # Verificar si ya existe la planta baja para esta construcción
                check_planta_sql = f"""
                    SELECT id_planta FROM catastro.construcciones_plantas19
                    WHERE id_construccion = {construccion_id} AND id_planta = 0
                """
                resultado_check = self.driver.read(sql=check_planta_sql, multi=False)
                
                if resultado_check:
                    print(f"La planta baja ya existe para la construcción ID: {construccion_id}")
                else:
                    # Obtener el siguiente ID disponible para planta baja
                    sql_ultimo_id_planta = "SELECT COALESCE(MAX(id), 0) + 1 AS proximo_id FROM catastro.construcciones_plantas19"
                    resultado_proximo_id = self.driver.read(sql=sql_ultimo_id_planta, multi=False)
                    proximo_id_planta = 1  # Valor por defecto
                    
                    if resultado_proximo_id:
                        if isinstance(resultado_proximo_id, dict) and 'proximo_id' in resultado_proximo_id:
                            proximo_id_planta = resultado_proximo_id['proximo_id']
                        elif hasattr(resultado_proximo_id, 'proximo_id'):
                            proximo_id_planta = resultado_proximo_id.proximo_id
                        else:
                            try:
                                proximo_id_planta = int(resultado_proximo_id[0])
                            except:
                                proximo_id_planta = 1
                    
                    # Crear la planta baja (id_planta = 0)
                    planta_baja_sql = f"""
                        INSERT INTO catastro.construcciones_plantas19 
                        (id, id_construccion, id_planta, anyo, superficie, geom)
                        SELECT 
                            {proximo_id_planta},
                            {construccion_id}, 
                            0,  -- Planta baja es 0
                            '{valor_anyo}', 
                            {cur_area}, 
                            geom  -- Mantener el SRID original sin transformar
                        FROM catastro.construcciones19
                        WHERE id = {construccion_id}
                    """
                    
                    try:
                        self.driver.create(sql=planta_baja_sql)
                        print(f"Planta baja creada para construcción ID: {construccion_id}")
                        plantas_creadas += 1
                    except Exception as e:
                        print(f"Error al crear planta baja: {str(e)}")
                
                # Calcular plantas adicionales correctamente
                # La planta baja ya es una planta, así que creamos num_plantas - 1 plantas adicionales
                plantas_adicionales = max(0, num_plantas - 1)  # Evitamos valores negativos
                
                # Crear plantas adicionales según el número especificado
                for i in range(1, plantas_adicionales + 1):
                    id_planta = i  # Primera planta adicional = 1, Segunda = 2, etc.
                    
                    # Verificar si ya existe esta planta
                    check_planta_sql = f"""
                        SELECT id_planta FROM catastro.construcciones_plantas19
                        WHERE id_construccion = {construccion_id} AND id_planta = {id_planta}
                    """
                    resultado_check = self.driver.read(sql=check_planta_sql, multi=False)
                    
                    if resultado_check:
                        print(f"La planta {id_planta} ya existe para la construcción ID: {construccion_id}")
                        continue
                    
                    # Obtener el siguiente ID disponible para esta planta
                    sql_ultimo_id_planta = "SELECT COALESCE(MAX(id), 0) + 1 AS proximo_id FROM catastro.construcciones_plantas19"
                    resultado_proximo_id = self.driver.read(sql=sql_ultimo_id_planta, multi=False)
                    proximo_id_planta = 1  # Valor por defecto
                    
                    if resultado_proximo_id:
                        if isinstance(resultado_proximo_id, dict) and 'proximo_id' in resultado_proximo_id:
                            proximo_id_planta = resultado_proximo_id['proximo_id']
                        elif hasattr(resultado_proximo_id, 'proximo_id'):
                            proximo_id_planta = resultado_proximo_id.proximo_id
                        else:
                            try:
                                proximo_id_planta = int(resultado_proximo_id[0])
                            except:
                                proximo_id_planta = 1
                    
                    planta_sql = f"""
                        INSERT INTO catastro.construcciones_plantas19 
                        (id, id_construccion, id_planta, anyo, superficie, geom)
                        SELECT 
                            {proximo_id_planta},
                            {construccion_id}, 
                            {id_planta}, 
                            '{valor_anyo}', 
                            {cur_area}, 
                            geom  -- Mantener el SRID original sin transformar
                        FROM catastro.construcciones19 
                        WHERE id = {construccion_id}
                    """
                    try:
                        self.driver.create(sql=planta_sql)
                        print(f"Planta {id_planta} creada para construcción ID: {construccion_id}")
                        plantas_creadas += 1
                    except Exception as e:
                        print(f"Error al crear planta {id_planta}: {str(e)}")
                
                # Mostrar mensaje de éxito
                if plantas_creadas > 0:
                    self.driver.showMessage(
                        f'Se crearon automáticamente {plantas_creadas} plantas', 
                        0, 5
                    )
                else:
                    self.driver.showMessage(
                        'No se crearon plantas adicionales (ya existían o hubo errores)', 
                        0, 3
                    )
        except Exception as ex:
            print(f"Error en crear_plantas_construccion: {str(ex)}")
            self.driver.showMessage(f'Error al crear plantas: {str(ex)}', 1, 15)
 
        
   
    def cargar_tablabbdd_construccion(self):
        try:
            list_widget = self.dlg_export_feature_construccion.list_bbdd
            
            # Limpiar el list widget
            for i in range(list_widget.count()):
                list_widget.takeItem(0)

            # Obtener datos de la base de datos
            sql = '''SELECT codigo, direccion 
                    FROM catastro.terrenos19 
                    ORDER BY codigo'''
            r = self.driver.read(sql=sql, multi=True)
            
            # Crear lista de items
            lista = [f"{item['codigo']}   {item['direccion']}" for item in r]
            
            # Agregar items al list widget
            list_widget.addItems(lista)
            
            self.driver.showMessage('Datos cargados exitosamente', 0, 3)
            
        except Exception as ex:
            print(f"Error en cargar_tablabbdd_construccion: {str(ex)}")
            self.driver.showMessage(f'Error al cargar datos: {str(ex)}', 1, 15)
    
    #GET A TERRENOS#############################################################################################################################################
    
        

            
        list_widget = self.dlg_export_feature_construccion.list_bbdd
        
        for i in range(list_widget.count()):
            list_widget.takeItem(0)

        sql = ''' SELECT *
        FROM catastro.terrenos19 '''

        r = self.driver.read(sql=sql, multi=True)
        lista = [str(item["codigo"]) + "   " + str(item["direccion"]) for item in r]
                
        list_widget.addItems(lista)
          
        
        
               
 #######################################AÑADIR EDIFICACION ESPECIAL##############################################################
               
               
    
    def cargar_tablabbdd_especial(self):
        list_widget_especial = self.dlg_export_especial.list_bbdd
        list_widget = self.dlg_export_feature_construccion.list_bbdd
        
        # Limpiar la lista especial
        for i in range(list_widget_especial.count()):
            list_widget_especial.takeItem(0)
        
        # Verificar si hay un elemento seleccionado
        current = list_widget.currentItem()
        if current is None:
            # No hay elemento seleccionado
            QMessageBox.warning(
                self.dlg_export_especial,
                "Advertencia",
                "Por favor, seleccione un elemento de la lista primero."
            )
            return
        
        # Si hay elemento seleccionado, continuar con el proceso
        currentText = current.text()
        currentTextSplit = currentText.split()
        currentTextSplitCodigo = currentTextSplit[0]
                
        r = self.driver.read(f''' select * from catastro.especialesvista19 where codigo = '{currentTextSplitCodigo}' ''')
    
        lista = [(str(item["nombre"]) +"    "+ str(item["codigo"])) for item in r]
    
        list_widget_especial.addItems(lista)      

    
    def guardar_feature_bbdd_especial(self,feature):
            
        list_widget = self.dlg_export_feature_construccion.list_bbdd
        current = list_widget.currentItem()
        
        #Obtengo el texto del QListWidgetItem
        list_widget_name = current.text()
        currentTextSplit = list_widget_name.split()
        currentTextSplitCodigo = currentTextSplit[0]
        
        tipo = self.dlg_export_especial.comboBox_tipo_edi.currentIndex() 
        
        anyo = self.dlg_export_especial.anyo
        valor_anyo = anyo.toPlainText()
        
        sup = self.dlg_export_especial.superficie
        valor_superficie = sup.toPlainText()
       
        conservacion = self.dlg_export_especial.comboBox_conservacion.currentIndex()  
        
        cimientos = self.dlg_export_especial.comboBox_cimientos.currentIndex()  
        estructura = self.dlg_export_especial.comboBox_estructura.currentIndex()  
        muros = self.dlg_export_especial.comboBox_muros.currentIndex()  
        externos = self.dlg_export_especial.comboBox_externos.currentIndex()  
        interiores = self.dlg_export_especial.comboBox_interiores.currentIndex()  
        techos = self.dlg_export_especial.comboBox_techos.currentIndex()  
        pisos = self.dlg_export_especial.comboBox_pisos.currentIndex()  
        ventanas = self.dlg_export_especial.comboBox_ventanas.currentIndex() 
        
        
        # urlTerrenosEspeciales19 = "http://192.168.0.150:8080/apiCatastro/terrenosespeciales19"
                
        
        # datos = {'anyo': valor_anyo, 'superficie': valor_superficie, 'conservacionBean': {'id': conservacion}, 'ediCarpinteria': {'id': ventanas},
        # 'ediCimiento':{'id': cimientos}, 'ediCubierta':{'id': techos}, 'ediEstructura': {'id': estructura},'ediMuro': {'id': muros},'ediMurosExt': {'id': externos},
        # 'ediMurosInt': {'id': interiores}, 'ediPiso': {'id': pisos}, 'especiale':{'id': tipo}, 'terrenos19': {'codigo': currentTextSplitCodigo}}
        
        # response = requests.post(urlTerrenosEspeciales19, json=datos)
        

        sql = f'''
        INSERT INTO catastro.terrenos_especiales19
        (codigo, id_esp, cimiento, estructura, muros, muros_ext, muros_int, cubierta, pisos, carpinteria, anyo, conservacion, superficie)
        VALUES('{currentTextSplitCodigo}', {tipo}, {cimientos}, {estructura}, {muros}, {externos}, {interiores} , {techos}, {pisos}, {ventanas}, '{valor_anyo}', {conservacion}, '{valor_superficie}');        
        '''
        
        try: 
            self.driver.create(sql)
        except Exception as ex: 
            print(ex)
        # if response.status_code == 201:
        #     print(response.content)
        #     QMessageBox.information(iface.mainWindow(), "Base de Datos", 'Información Guardada en la Base de Datos Correctamente')
        # else:
        #     QMessageBox.information(iface.mainWindow(), "Base de Datos", 'No se pude cargar la información en la Base de Datos') 
            
        
        self.dlg_export_especial.comboBox_tipo_edi.setCurrentIndex(0)
        self.dlg_export_especial.anyo.clear()         
        sup = self.dlg_export_especial.superficie.clear() 
        self.dlg_export_especial.comboBox_conservacion.setCurrentIndex(0)
        
        self.dlg_export_especial.comboBox_cimientos.setCurrentIndex(0) 
        self.dlg_export_especial.comboBox_estructura.setCurrentIndex(0) 
        self.dlg_export_especial.comboBox_muros.setCurrentIndex(0)
        self.dlg_export_especial.comboBox_externos.setCurrentIndex(0)  
        self.dlg_export_especial.comboBox_interiores.setCurrentIndex(0)
        self.dlg_export_especial.comboBox_techos.setCurrentIndex(0) 
        self.dlg_export_especial.comboBox_pisos.setCurrentIndex(0)  
        self.dlg_export_especial.comboBox_ventanas.setCurrentIndex(0)
        
                 
               
               
               ######################################AÑADIR MEJORA#########################################################################
                             
        
    def cargar_tablabbdd_mejora(self):
    
   
        urlTerrenosMejoras19 = "http://192.168.0.150:8080/apiCatastro/terrenosmejoras19"
        
        # response = requests.get(urlTerrenosMejoras19)
        
        # responseArray = []
        
        # if response.status_code == 200:
        #     response_json = response.json()
            
        list_widget_mejora = self.dlg_export_mejora.list_bbdd
        
        list_widget = self.dlg_export_feature_construccion.list_bbdd
        current = list_widget.currentItem()
        # list_widget_name = current.text()
        
        
        for i in range(list_widget_mejora.count()):
            list_widget_mejora.takeItem(0)
        
        lista = []
        
        print("CURRENTE")
        currentText = current.text()
        currentTextSplit = currentText.split()
        currentTextSplitCodigo = currentTextSplit[0]
        print(currentTextSplitCodigo)
        
        r = self.driver.read(f''' select * from catastro.mejorasvista19 where codigo = '{currentTextSplitCodigo}' ''')
        
        lista = [(str(item["nombre"]) +"    "+ str(item["codigo"])) for item in r]
       
        list_widget_mejora.addItems(lista)
 
               
    
    def guardar_feature_bbdd_mejora(self,feature):
    
    
        list_widget = self.dlg_export_feature_construccion.list_bbdd
        current = list_widget.currentItem()
        
        
        #Obtengo el texto del QListWidgetItem
        list_widget_name = current.text()
        currentTextSplit = list_widget_name.split()
        currentTextSplitCodigo = currentTextSplit[0]
        
    
        tipo = self.dlg_export_mejora.comboBox_tipo_mejora.currentIndex() 
        
        anyo = self.dlg_export_mejora.anyo
        valor_anyo = anyo.toPlainText()
        
        sup = self.dlg_export_mejora.superficie
        valor_superficie = sup.toPlainText()
       
        conservacion = self.dlg_export_mejora.comboBox_conservacion.currentIndex()  
        
        cimientos = self.dlg_export_mejora.comboBox_cimientos.currentIndex()  
        estructura = self.dlg_export_mejora.comboBox_estructura.currentIndex()  
        muros = self.dlg_export_mejora.comboBox_muros.currentIndex()  
        externos = self.dlg_export_mejora.comboBox_externos.currentIndex()  
        interiores = self.dlg_export_mejora.comboBox_interiores.currentIndex()  
        techos = self.dlg_export_mejora.comboBox_techos.currentIndex()  
        pisos = self.dlg_export_mejora.comboBox_pisos.currentIndex()  
        ventanas = self.dlg_export_mejora.comboBox_ventanas.currentIndex()
        
  
  
        #urlTerrenosMejoras19 = "http://192.168.0.150:8080/apiCatastro/terrenosmejoras19"
                
        datos = {'anyo': valor_anyo, 'superficie': valor_superficie, 'conservacionBean': {'id': conservacion}, 'ediCarpinteria': {'id': ventanas},
        'ediCimiento':{'id': cimientos}, 'ediCubierta':{'id': techos}, 'ediEstructura': {'id': estructura},'ediMuro': {'id': muros},'ediMurosExt': {'id': externos},
        'ediMurosInt': {'id': interiores}, 'ediPiso': {'id': pisos}, 'mejora':{'id': tipo}, 'terrenos19': {'codigo': currentTextSplitCodigo}}
        
        response = requests.post(urlTerrenosMejoras19, json=datos)
        
        
        if response.status_code == 201:
            print(response.content)
            QMessageBox.information(iface.mainWindow(), "Base de Datos", 'Información Guardada en la Base de Datos Correctamente')
        else:
            QMessageBox.information(iface.mainWindow(), "Base de Datos", 'No se pude cargar la información en la Base de Datos') 
  
        
        
        self.dlg_export_mejora.comboBox_tipo_mejora.setCurrentIndex(0)
        self.dlg_export_mejora.anyo.clear() 
        self.dlg_export_mejora.superficie.clear() 

        self.dlg_export_mejora.comboBox_conservacion.setCurrentIndex(0)
        
        self.dlg_export_mejora.comboBox_cimientos.setCurrentIndex(0)
        self.dlg_export_mejora.comboBox_estructura.setCurrentIndex(0) 
        self.dlg_export_mejora.comboBox_muros.setCurrentIndex(0) 
        self.dlg_export_mejora.comboBox_externos.setCurrentIndex(0) 
        self.dlg_export_mejora.comboBox_interiores.setCurrentIndex(0)
        self.dlg_export_mejora.comboBox_techos.setCurrentIndex(0)
        self.dlg_export_mejora.comboBox_pisos.setCurrentIndex(0)  
        self.dlg_export_mejora.comboBox_ventanas.setCurrentIndex(0)
    
               
        
 
        ################################################################################################################################################
        #################################################################################################################################################
        ######################################################     AÑADIR PLANTA      ####################################################################
        #################################################################################################################################################
        #################################################################################################################################################
            
            
            
    construcciones_cargadas = ""
 
    def cargar_tablaconstruccionbd_plantas(self):
        try:
            print("DEBUG: Iniciando carga de construcciones")
            list_widget = self.dlg_listar_construccion_plantas.list_bbdd
            list_widget.clear()
            
            # Obtener datos de construcciones
            sql = """
                SELECT cv.id, cv.numbloque, cv.codigo, cv.superficie, cv.nombreuso, cv.anyo, cv.tipoconstruccion,
                    c.numplanta
                FROM catastro.construccionesvista19 cv
                LEFT JOIN catastro.construcciones19 c ON cv.id = c.id
                ORDER BY cv.codigo, cv.numbloque
            """
            resultados = self.driver.read(sql)
            print(f"DEBUG: {len(resultados)} construcciones encontradas")
            
            for item in resultados:
                try:
                    # Crear texto para mostrar
                    texto = f"{item['id']}    {item['numbloque']}    {item['codigo']}    {item['nombreuso']}"
                    list_item = QListWidgetItem(texto)
                    
                    # Guardar datos completos en el UserRole
                    list_item.setData(Qt.UserRole, item)
                    
                    # Si ya tiene planta, cambiar el color del texto a gris
                    if item.get('numplanta'):
                        list_item.setForeground(Qt.gray)
                    
                    # Agregar item a la lista
                    list_widget.addItem(list_item)
                    
                except Exception as e:
                    print(f"ERROR procesando item: {str(e)}")
                    continue
            
            self.construcciones_cargadas = resultados
            
            # NUEVO: Actualizar también los datos internos en la clase ListarConstruccionPlantas
            if hasattr(self.dlg_listar_construccion_plantas, 'update_with_external_data'):
                self.dlg_listar_construccion_plantas.update_with_external_data(resultados)
                print("✅ Datos sincronizados con ListarConstruccionPlantas")
            
            print(f"DEBUG: Lista cargada con {list_widget.count()} items")
            
        except Exception as e:
            print(f"ERROR en cargar_tablaconstruccionbd_plantas: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
    def planta_busca_ref(self):
        list_widget = self.dlg_listar_construccion_plantas.list_bbdd
        text_busqueda = self.dlg_select_construccion_planta_busca_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText().strip()
        
        # Consulta modificada para tomar solo el registro más reciente por bloque
        sql = f'''
            WITH RankedConstrucciones AS (
                SELECT id, numbloque, codigo, superficie, tipoconstruccion, 
                    nombreuso, anyo,
                    ROW_NUMBER() OVER (PARTITION BY numbloque ORDER BY id DESC) as rn
                FROM catastro.construccionesvista19 
                WHERE codigo = '{valor_busqueda}'
            )
            SELECT id, numbloque, codigo, superficie, tipoconstruccion, 
                nombreuso, anyo
            FROM RankedConstrucciones
            WHERE rn = 1
            ORDER BY numbloque
        '''
        
        r = self.driver.read(sql)
        print(f"Registros encontrados (un registro por bloque): {len(r)}")
        
        list_widget.clear()
        
        if len(r) > 0:
            lista = []
            for item in r:
                try:
                    superficie = f"{float(item['superficie']):.2f}" if item['superficie'] else "N/A"
                    tipo = item['tipoconstruccion'] if item['tipoconstruccion'] else "Sin definir"
                    uso = item['nombreuso'] if item['nombreuso'] else "Sin definir"
                    
                    registro = (f"{item['id']} | "
                            f"Bloque: {item['numbloque']} | "
                            f"Sup: {superficie}m² | "
                            f"Tipo: {tipo} | "
                            f"Uso: {uso} | "
                            f"Año: {item['anyo']}")
                    lista.append(registro)
                    print(f"Procesando registro único: {registro}")
                except Exception as e:
                    print(f"Error procesando registro: {str(e)}")
                    continue
            
            if lista:
                list_widget.addItems(lista)
                list_widget.setCurrentRow(0)
            else:
                self.driver.showMessage('Error al procesar los registros.',1,15)
        else: 
            self.driver.showMessage('No existen registros con la referencia Catastral.',1,15)
    
    
    def cargar_plantas(self):
        """Carga las plantas para la construcción seleccionada"""
        try:
            # Verificar qué tipo de objeto es self.dlg_export_planta
            print(f"Tipo de dlg_export_planta: {type(self.dlg_export_planta).__name__}")
            
            # Si es ExportDatabasePlantas, no tiene list_bbdd
            if isinstance(self.dlg_export_planta, ExportDatabasePlantas):
                print("Detectada clase ExportDatabasePlantas - no contiene list_bbdd")
                # Usar otra función o atributo apropiado para esta clase
                # Por ejemplo, si esta clase tiene otro método para cargar plantas:
                if hasattr(self.dlg_export_planta, 'cargar_plantas_existentes'):
                    construccion_id = self.dlg_listar_construccion_plantas.construccion_seleccionada
                    if construccion_id:
                        self.dlg_export_planta.cargar_plantas_existentes()
                        return
                
                print("No se puede cargar plantas con esta clase")
                return
                
            # Si es ExportPlantas, podría tener otros atributos
            elif hasattr(self.dlg_export_planta, 'construccion_data'):
                print("Usando propiedades alternativas para cargar plantas")
                # Usar métodos de la clase correcta
                if hasattr(self.dlg_export_planta, 'cargar_datos_planta_baja'):
                    self.dlg_export_planta.cargar_datos_planta_baja()
                    return
            
            # Si código llega aquí, hay un problema con la clase
            print("ERROR: La clase de dlg_export_planta no es compatible")
            
        except Exception as e:
            print(f"Error en cargar_plantas: {str(e)}")
            import traceback
            traceback.print_exc()    
    
    def guardar_planta(self, construccion_id, id_planta, anyo, superficie, muros_ext=1, muros_int=1, pisos=1, geom=None):
        """
        Función mejorada para guardar o actualizar una planta con todos los campos necesarios
        
        Args:
            construccion_id: ID de la construcción
            id_planta: Número de planta (0 para planta baja, 1+ para plantas adicionales)
            anyo: Año de construcción
            superficie: Superficie en m²
            muros_ext: Valor para muros exteriores (por defecto 1)
            muros_int: Valor para muros interiores (por defecto 1)
            pisos: Valor para pisos (por defecto 1)
            geom: Geometría WKT (opcional)
        
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            # Validar parámetros
            if not construccion_id or id_planta is None:
                print("ERROR: ID de construcción o planta inválido")
                return False
                
            # Verificar si la planta ya existe
            check_sql = f"""
                SELECT id_planta
                FROM catastro.construcciones_plantas19
                WHERE id_construccion = {construccion_id}
                AND id_planta = {id_planta};
            """
            planta_existe = self.driver.read(check_sql, multi=False)
            
            # Preparar la parte de geometría SQL si existe
            geom_sql = f", geom = ST_GeomFromText('{geom}', 4326)" if geom else ""
            
            if planta_existe:
                # Actualizar planta existente
                update_sql = f"""
                    UPDATE catastro.construcciones_plantas19
                    SET anyo = '{anyo}',
                        superficie = {superficie},
                        muros_ext = {muros_ext},
                        muros_int = {muros_int},
                        pisos = {pisos}
                        {geom_sql}
                    WHERE id_construccion = {construccion_id}
                    AND id_planta = {id_planta};
                """
                self.driver.update(update_sql)
                print(f"Planta {id_planta} actualizada correctamente")
            else:
                # Primero, obtener el próximo ID disponible para la planta
                sql_ultimo_id_planta = "SELECT COALESCE(MAX(id), 0) + 1 AS proximo_id FROM catastro.construcciones_plantas19"
                resultado_proximo_id = self.driver.read(sql=sql_ultimo_id_planta, multi=False)
                proximo_id_planta = 1  # Valor por defecto
                
                if resultado_proximo_id:
                    if isinstance(resultado_proximo_id, dict) and 'proximo_id' in resultado_proximo_id:
                        proximo_id_planta = resultado_proximo_id['proximo_id']
                    elif hasattr(resultado_proximo_id, 'proximo_id'):
                        proximo_id_planta = resultado_proximo_id.proximo_id
                    else:
                        try:
                            proximo_id_planta = int(resultado_proximo_id[0])
                        except:
                            proximo_id_planta = 1
                
                print(f"Usando próximo ID para planta: {proximo_id_planta}")
                
                # Insertar nueva planta CON UN ID EXPLÍCITO
                if geom:
                    insert_sql = f"""
                        INSERT INTO catastro.construcciones_plantas19 
                        (id, id_construccion, id_planta, anyo, superficie, muros_ext, muros_int, pisos, geom)
                        VALUES (
                            {proximo_id_planta},
                            {construccion_id},
                            {id_planta},
                            '{anyo}',
                            {superficie},
                            {muros_ext},
                            {muros_int},
                            {pisos},
                            ST_GeomFromText('{geom}', 4326)
                        );
                    """
                else:
                    insert_sql = f"""
                        INSERT INTO catastro.construcciones_plantas19 
                        (id, id_construccion, id_planta, anyo, superficie, muros_ext, muros_int, pisos)
                        VALUES (
                            {proximo_id_planta},
                            {construccion_id},
                            {id_planta},
                            '{anyo}',
                            {superficie},
                            {muros_ext},
                            {muros_int},
                            {pisos}
                        );
                    """
                
                try:
                    self.driver.create(insert_sql)
                    print(f"Planta {id_planta} creada correctamente con ID: {proximo_id_planta}")
                except Exception as e:
                    print(f"ERROR al crear planta {id_planta}: {str(e)}")
                    # Si el error es de geometría, intentar sin ella
                    if "geom" in str(e).lower() and geom:
                        print("Intentando guardar sin geometría...")
                        return self.guardar_planta(construccion_id, id_planta, anyo, superficie, 
                                                muros_ext, muros_int, pisos, None)
                    return False
                    
            # Actualizar el contador de plantas en construcciones19
            self.actualizar_total_plantas(construccion_id)
            return True
            
        except Exception as e:
            print(f"ERROR en guardar_planta: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def cargar_datos_construccion(self, construccion_id):
        try:
            sql = f'''
                SELECT nombreuso
                FROM catastro.construccionesvista19 
                WHERE id = {construccion_id}
            '''
            r = self.driver.read(sql)
            
            if r:
                uso_actual = r[0]['nombreuso']
                combo_uso = self.dlg_export_database_feature_construccion.comboBox_uso
                
                # Encontrar y seleccionar el uso en el ComboBox
                index = combo_uso.findText(uso_actual)
                if index >= 0:
                    combo_uso.setCurrentIndex(index)
                else:
                    combo_uso.setCurrentIndex(0)  # Valor vacío si no se encuentra
                    
        except Exception as e:
            print(f"Error al cargar uso: {str(e)}")
        
           
    def setup_ui_connections(self):
        try:
            # Conectar el botón para mostrar el formulario de plantas
            if hasattr(self.dlg_listar_construccion_plantas, 'btn_agregar_planta'):
                self.dlg_listar_construccion_plantas.btn_agregar_planta.clicked.connect(self.abrir_formulario_plantas)
                print("Conexión de botón agregar planta establecida")
                
            # NUEVO: Conectar el botón de informe a un método en esta clase
            if hasattr(self.dlg_listar_construccion_plantas, 'btn_informe'):
                # Desconectar cualquier conexión previa que pueda causar errores
                try:
                    self.dlg_listar_construccion_plantas.btn_informe.clicked.disconnect()
                except:
                    pass
                    
                # Conectar a un método en esta clase
                self.dlg_listar_construccion_plantas.btn_informe.clicked.connect(self.generar_informe_construccion)
                print("Conexión de botón informe establecida correctamente")
        except Exception as e:
            print(f"Error en setup_ui_connections: {str(e)}")
            
    # NUEVO: Método para manejar el clic en el botón de informe
    def generar_informe_construccion(self):
        """Maneja el evento de clic en el botón 'Informe'."""
        try:
            construccion_id = self.dlg_listar_construccion_plantas.construccion_seleccionada
            
            if not construccion_id:
                self.driver.showMessage("Seleccione una construcción primero", 1, 5)
                return
                
            # Verificar si existen datos para esta construcción
            check_sql = f"""
                SELECT c.id 
                FROM catastro.construcciones19 c
                WHERE c.id = {construccion_id};
            """
            # Usar self.driver directamente
            construccion_existe = self.driver.read(check_sql, multi=False)
            
            if not construccion_existe:
                self.driver.showMessage("La construcción seleccionada no existe en la base de datos", 1, 5)
                return
                
            # Verificar si tiene plantas registradas
            check_plantas_sql = f"""
                SELECT COUNT(*) as total
                FROM catastro.construcciones_plantas19 cp
                WHERE cp.id_construccion = {construccion_id};
            """
            result = self.driver.read(check_plantas_sql, multi=False)
            total_plantas = result.get('total', 0) if result else 0
            
            if total_plantas == 0:
                self.driver.showMessage("Debe agregar al menos una planta a esta construcción primero", 1, 5)
                return
                
            # Aquí puedes implementar la lógica para generar el informe
            # Por ejemplo, podrías abrir un diálogo específico para informes
            
            # Ejemplo (ajustar según tus necesidades):
            self.driver.showMessage("Generando informe para construcción ID: " + str(construccion_id), 0, 3)
            
        except Exception as e:
            print(f"ERROR al generar informe: {str(e)}")
            import traceback
            traceback.print_exc()
            self.driver.showMessage(f"Error al generar informe: {str(e)}", 1, 5)        
    
    def abrir_dialogo_listarconstruccion_plantas(self):
        self.dlg_listar_construccion_plantas.show()
        self.cargar_tablaconstruccionbd_plantas()
    
    def abrir_formulario_plantas(self):
        # Obtener el ID de construcción seleccionada
        construccion_id = self.dlg_listar_construccion_plantas.construccion_seleccionada
        
        if not construccion_id:
            self.driver.showMessage("Seleccione una construcción primero", 1, 5)
            return
        
        # Crear el diálogo con el ID de construcción
        dlg = self.get_export_database_plantas_dialog(construccion_id)
        
        if dlg:
            # Ahora puedes conectar el evento directamente aquí si es necesario
            dlg.accepted.connect(self.cerrar_dialogo_exportbbdd_planta)
            
            if dlg.exec_() == QDialog.Accepted:
                # Código a ejecutar cuando se acepta el diálogo
                print("Planta guardada correctamente")
        else:
            self.driver.showMessage("Error al crear el diálogo de plantas", 1, 5)
     
    
    def actualizar_total_plantas(self, construccion_id):
        try:
            # Contar plantas existentes EXCLUYENDO la planta baja (id_planta = 0)
            sql = f'''
                SELECT COUNT(*) as total_adicionales
                FROM catastro.construcciones_plantas19
                WHERE id_construccion = {construccion_id}
                AND id_planta > 0
            '''
            r = self._driver.read(sql)
            total_plantas_adicionales = r[0]['total_adicionales']
            
            # También verificar si existe la planta baja
            sql_planta_baja = f'''
                SELECT COUNT(*) as tiene_planta_baja
                FROM catastro.construcciones_plantas19
                WHERE id_construccion = {construccion_id}
                AND id_planta = 0
            '''
            r_baja = self._driver.read(sql_planta_baja)
            tiene_planta_baja = r_baja[0]['tiene_planta_baja'] > 0
            
            # Calcular el número correcto de plantas
            # Si tiene planta baja, se cuenta como 1 planta
            total_plantas = total_plantas_adicionales
            if tiene_planta_baja:
                total_plantas += 1
            
            # Asegurar que siempre hay al menos 1 planta
            if total_plantas < 1:
                total_plantas = 1
                
            # Actualizar en construcciones19
            sql_update = f'''
                UPDATE catastro.construcciones19
                SET numplanta = {total_plantas}
                WHERE id = {construccion_id}
            '''
            self._driver.execute(sql_update)
            
            print(f"Total de plantas actualizado correctamente a {total_plantas}")
            
        except Exception as e:
            print(f"Error al actualizar total de plantas: {str(e)}")

    def limpiar_formulario_plantas(self):
        try:
            # Limpiar todos los campos del formulario
            self.dlg_export_plantas.comboBox_planta.setCurrentIndex(0)
            self.dlg_export_plantas.anyo.clear()
            self.dlg_export_plantas.superficie.clear()
            self.dlg_export_plantas.comboBox_cimientos.setCurrentIndex(0)
            self.dlg_export_plantas.comboBox_estructura.setCurrentIndex(0)
            self.dlg_export_plantas.comboBox_muros.setCurrentIndex(0)
            self.dlg_export_plantas.comboBox_externos.setCurrentIndex(0)
            self.dlg_export_plantas.comboBox_interiores.setCurrentIndex(0)
            self.dlg_export_plantas.comboBox_techos.setCurrentIndex(0)
            self.dlg_export_plantas.comboBox_pisos.setCurrentIndex(0)
            self.dlg_export_plantas.comboBox_ventanas.setCurrentIndex(0)
            
            # Resetear el ID de construcción actual
            self.dlg_export_plantas.construccion_actual_id = None
            
            print("DEBUG: Formulario limpiado correctamente")
        except Exception as e:
            print(f"ERROR al limpiar formulario: {str(e)}")
        
    
        
     
     
     
     
   
    ############################################################################################################################################
    ############################################################CUARTO BOTON DIBUJA LAYOUT##########################################################
    ############################################################################################################################################ 






    
    terrenos_cargados_layout = ""
          
    def cargar_tablabbdd(self):
      
        list_widget = self.dlg_layout.list_bbdd
        
        for i in range(list_widget.count()):
            list_widget.takeItem(0)
        
        r = self.driver.read('select codigo, nombre, apellidos, documento from catastro.terrenosvista19')
        # print(r)
        
        
        lista = []
                
        for item in r:

            if item["nombre"] or item["apellidos"]:

                lista.append(str(item["codigo"]) + "   " + str(item["nombre"])  + "   " + str(item["apellidos"]))
            else:
                lista.append(str(item["codigo"]))
       
        list_widget.addItems(lista)
        
        self.terrenos_cargados_layout = r
      
    def listar_layer_busca_ref(self):
                        
        list_widget = self.dlg_layout.list_bbdd
            
       
            
        text_busqueda  = self.dlg_select_terreno_layout_busca_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText()
            

        r = self.driver.read(f''' select codigo, nombre, apellidos, documento from catastro.terrenosvista19 where codigo ilike '%{valor_busqueda}%' ''')

        if len(r) > 0 :
            for i in range(list_widget.count()):
                list_widget.takeItem(0)
            lista = [str(item["codigo"]) + "   " + str(item["nombre"]) + " " + str(item["apellidos"]) for item in r]
            list_widget.addItems(lista)
        else: 
            self.driver.showMessage('No existen registros con este Codigo Catastral .',1,15)
        
    
    def listar_layer_busca_nombre(self):
            
        list_widget = self.dlg_layout.list_bbdd
            
        text_busqueda  = self.dlg_select_terreno_layout_busca_nombre.text_titular
        valor_busqueda = text_busqueda.toPlainText()
            
        
        try: 
            q = ''
            for e in valor_busqueda.split(): 
                q  = q + '%' + e + '% '

            sql = f''' select codigo, nombre, apellidos, documento from catastro.terrenosvista19 where nombre || ' ' || apellidos ilike '{q[:-1]}' '''
            r = self.driver.read(sql)
            if len(r) > 0:
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                lista = [str(item["codigo"]) + "   " + str(item["nombre"]) + " " + str(item["apellidos"]) for item in r]
                list_widget.addItems(lista)
            else: 
                self.driver.showMessage('No existen registros con los valores buscados.',1,15)
                    

        except Exception as ex: 
            print(ex)
    
    def calcular_ancho_calle_mejorado(self, feature_terreno, terreno_id):
        """
        Calcula el ancho de calle utilizando un algoritmo mejorado que detecta
        frentes y esquinas, calculando anchuras perpendiculares precisas.
        """
        try:
            # Obtener el manzano actual
            manzano_actual = None
            if feature_terreno.fieldNameIndex('manzano') != -1:
                manzano_actual = feature_terreno['manzano']
            else:
                # Intentar extraer del código
                try:
                    partes = str(terreno_id).split('.')
                    if len(partes) >= 3:
                        manzano_actual = partes[2]
                except:
                    print("No se pudo extraer el manzano del código")
            
            print(f"Calculando ancho de calle para terreno: {terreno_id} (Manzano: {manzano_actual})")
            
            # Usar SQL directamente para todos los cálculos
            sql_avanzado = f"""
            WITH 
            -- Obtener el terreno
            terreno AS (
                SELECT 
                    geom, 
                    manzano
                FROM 
                    catastro.terrenos19
                WHERE 
                    codigo = '{terreno_id}'
            ),
            -- Obtener el contorno del terreno como segmentos individuales
            segmentos AS (
                SELECT 
                    ST_MakeLine(
                        ST_PointN(ST_ExteriorRing(geom), n),
                        ST_PointN(ST_ExteriorRing(geom), n+1)
                    ) AS segmento_geom,
                    n AS indice,
                    ST_Length(
                        ST_MakeLine(
                            ST_PointN(ST_ExteriorRing(geom), n),
                            ST_PointN(ST_ExteriorRing(geom), n+1)
                        )
                    ) AS longitud,
                    ST_X(ST_PointN(ST_ExteriorRing(geom), n)) AS x1,
                    ST_Y(ST_PointN(ST_ExteriorRing(geom), n)) AS y1,
                    ST_X(ST_PointN(ST_ExteriorRing(geom), n+1)) AS x2,
                    ST_Y(ST_PointN(ST_ExteriorRing(geom), n+1)) AS y2
                FROM 
                    terreno,
                    generate_series(1, ST_NPoints(ST_ExteriorRing(geom))-1) AS n
                WHERE 
                    ST_Length(
                        ST_MakeLine(
                            ST_PointN(ST_ExteriorRing(geom), n),
                            ST_PointN(ST_ExteriorRing(geom), n+1)
                        )
                    ) > 1.0  -- Ignorar segmentos muy cortos
            ),
            -- Calcular el centroide de cada segmento
            centroides AS (
                SELECT 
                    indice,
                    segmento_geom,
                    longitud,
                    ST_Centroid(segmento_geom) AS centroide_geom,
                    ST_X(ST_Centroid(segmento_geom)) AS centroide_x,
                    ST_Y(ST_Centroid(segmento_geom)) AS centroide_y,
                    -- Normalizar vector director
                    (x2 - x1) / longitud AS dx,
                    (y2 - y1) / longitud AS dy,
                    -- Vector perpendicular
                    (y1 - y2) / longitud AS perp_x,
                    (x2 - x1) / longitud AS perp_y
                FROM 
                    segmentos
            ),
            -- Generar proyecciones perpendiculares
            proyecciones AS (
                SELECT 
                    indice,
                    segmento_geom,
                    longitud,
                    centroide_geom,
                    -- Generar proyección perpendicular (100 metros)
                    ST_MakeLine(
                        centroide_geom,
                        ST_SetSRID(
                            ST_MakePoint(
                                centroide_x + perp_x * 100,
                                centroide_y + perp_y * 100
                            ),
                            32719
                        )
                    ) AS proyeccion_pos,
                    -- Generar proyección en dirección opuesta
                    ST_MakeLine(
                        centroide_geom,
                        ST_SetSRID(
                            ST_MakePoint(
                                centroide_x - perp_x * 100,
                                centroide_y - perp_y * 100
                            ),
                            32719
                        )
                    ) AS proyeccion_neg
                FROM 
                    centroides
            ),
            -- Encontrar manzanos que intersectan con las proyecciones
            intersecciones AS (
                SELECT 
                    p.indice,
                    p.longitud,
                    'pos' AS direccion,
                    m.manzana,
                    ST_Distance(p.centroide_geom, m.geom) AS distancia
                FROM 
                    proyecciones p
                CROSS JOIN 
                    terreno t
                JOIN 
                    catastro.manzanos m ON ST_Intersects(p.proyeccion_pos, m.geom)
                WHERE 
                    m.manzana != t.manzano
                
                UNION ALL
                
                SELECT 
                    p.indice,
                    p.longitud,
                    'neg' AS direccion,
                    m.manzana,
                    ST_Distance(p.centroide_geom, m.geom) AS distancia
                FROM 
                    proyecciones p
                CROSS JOIN 
                    terreno t
                JOIN 
                    catastro.manzanos m ON ST_Intersects(p.proyeccion_neg, m.geom)
                WHERE 
                    m.manzana != t.manzano
            ),
            -- Seleccionar la intersección más cercana para cada segmento
            mejores_intersecciones AS (
                SELECT DISTINCT ON (indice)
                    indice,
                    longitud,
                    direccion,
                    manzana,
                    distancia
                FROM 
                    intersecciones
                ORDER BY 
                    indice, distancia ASC
            ),
            -- Calcular también la proyección diagonal desde la esquina
            punto_esquina AS (
                SELECT 
                    ST_PointN(ST_ExteriorRing(geom), 2) AS esquina_geom
                FROM 
                    terreno
            ),
            proyeccion_diagonal AS (
                SELECT 
                    pe.esquina_geom,
                    -- Proyección a 45 grados
                    ST_MakeLine(
                        esquina_geom,
                        ST_SetSRID(
                            ST_MakePoint(
                                ST_X(esquina_geom) + 100 * cos(radians(45)),
                                ST_Y(esquina_geom) + 100 * sin(radians(45))
                            ),
                            32719
                        )
                    ) AS proyeccion_diag
                FROM 
                    punto_esquina pe
            ),
            -- Intersección diagonal
            interseccion_diagonal AS (
                SELECT 
                    m.manzana,
                    ST_Distance(pd.esquina_geom, m.geom) AS distancia
                FROM 
                    proyeccion_diagonal pd
                CROSS JOIN 
                    terreno t
                JOIN 
                    catastro.manzanos m ON ST_Intersects(pd.proyeccion_diag, m.geom)
                WHERE 
                    m.manzana != t.manzano
                ORDER BY 
                    distancia ASC
                LIMIT 1
            )
            -- Resultados finales
            SELECT 
                mi.indice,
                mi.manzana,
                -- Ajustar valores a rangos razonables
                CASE
                    WHEN mi.distancia < 5 THEN 5
                    WHEN mi.distancia > 60 THEN 60
                    ELSE mi.distancia
                END AS ancho,
                -- Usar el promedio como ancho general
                (SELECT 
                    CASE
                        WHEN COUNT(*) > 0 THEN AVG(
                            CASE
                                WHEN distancia < 5 THEN 5
                                WHEN distancia > 60 THEN 60
                                ELSE distancia
                            END
                        )
                        ELSE 26.30
                    END
                FROM mejores_intersecciones
                ) AS ancho_promedio,
                -- Incluir el ancho diagonal si existe
                (SELECT 
                    CASE
                        WHEN distancia < 5 THEN 5
                        WHEN distancia > 60 THEN 60
                        ELSE distancia
                    END
                FROM interseccion_diagonal
                LIMIT 1
                ) AS ancho_diagonal
            FROM 
                mejores_intersecciones mi
            ORDER BY 
                mi.longitud DESC
            LIMIT 10
            """
            
            # Ejecutar la consulta
            result = self.driver.read(sql_avanzado, multi=True)
            
            if not result or len(result) == 0:
                print("No se encontraron resultados en el cálculo avanzado, usando método alternativo")
                # Método antiguo como fallback
                sql_distancia = f"""
                SELECT 
                    manzana, 
                    ST_Distance(
                        (SELECT geom FROM catastro.terrenos19 WHERE codigo = '{terreno_id}'),
                        m.geom
                    ) as distancia
                FROM catastro.manzanos m
                WHERE 
                    manzana != '{manzano_actual}' AND
                    ST_DWithin(
                        (SELECT geom FROM catastro.terrenos19 WHERE codigo = '{terreno_id}'),
                        m.geom,
                        100
                    )
                ORDER BY distancia ASC
                LIMIT 1
                """
                
                result_alt = self.driver.read(sql_distancia, multi=False)
                
                if result_alt and 'distancia' in result_alt and result_alt['distancia'] is not None:
                    ancho_calle = round(result_alt['distancia'], 2)
                    
                    # Validar que sea un valor razonable
                    if ancho_calle < 5:
                        ancho_calle = 10
                    elif ancho_calle > 60:
                        ancho_calle = 30
                else:
                    ancho_calle = 26.30  # Valor predeterminado
                    print("No se encontraron manzanos cercanos. Usando valor predeterminado.")
                    self.driver.showMessage("No se encontraron manzanos cercanos. Usando valor predeterminado.", 1, 3)
                
                print(f"Ancho de calle calculado (método alternativo): {ancho_calle} metros")
                
                # Actualizar la columna ancho_calle en todos los ejes viales cercanos
                sql_update = f"""
                UPDATE catastro.ejevias SET ancho_calle = {ancho_calle}
                WHERE ST_DWithin(
                    geom, 
                    (SELECT geom FROM catastro.terrenos19 WHERE codigo = '{terreno_id}'),
                    30
                )
                """
                self.driver.update(sql_update, msg=False)
                
                return ancho_calle
            
            # Mostrar resultados
            ancho_promedio = result[0]['ancho_promedio'] if 'ancho_promedio' in result[0] else None
            ancho_diagonal = result[0]['ancho_diagonal'] if 'ancho_diagonal' in result[0] else None
            
            print("Resultados del cálculo de ancho de calle:")
            for r in result:
                print(f"Lado {r['indice']} -> Manzano {r['manzana']}: Ancho = {r['ancho']}m")
            
            if ancho_diagonal:
                print(f"Ancho diagonal: {ancho_diagonal}m")
            
            ancho_final = ancho_promedio if ancho_promedio else result[0]['ancho']
            ancho_final = round(ancho_final, 2)
            
            print(f"Ancho de calle calculado (promedio): {ancho_final} metros")
            self.driver.showMessage(f"Ancho de calle calculado: {ancho_final} m", 0, 3)
            
            # Actualizar la columna ancho_calle en todos los ejes viales cercanos
            sql_update = f"""
            UPDATE catastro.ejevias SET ancho_calle = {ancho_final}
            WHERE ST_DWithin(
                geom, 
                (SELECT geom FROM catastro.terrenos19 WHERE codigo = '{terreno_id}'),
                30
            )
            """
            self.driver.update(sql_update, msg=False)
            
            return ancho_final
            
        except Exception as e:
            import traceback
            print(f"Error en calcular_ancho_calle_mejorado: {str(e)}")
            print(traceback.format_exc())
            self.driver.showMessage(f"Error al calcular ancho de calle: {str(e)}", 2, 5)
            return 26.30  # Valor predeterminado en caso de error    
    
    def getColindantes(self,codigo):

        sql = '''with parcela as (select t.* from catastro.terrenosvista19 t where t.codigo = '{}'),
colindantes as (select v.* from parcela p join catastro.terrenosvista19 v on st_touches(p.geom,v.geom) and v.codigo != p.codigo),
anillos AS (-- Extraer anillos de cada poligono
SELECT
  (ST_Dump(st_exteriorring(st_geometryn((st_dump(geom)).geom,1)))).geom AS geom
FROM parcela
),
segmentos AS (-- Extraer segmentos de cada anillo
SELECT
  generate_series(1, ST_NPoints(geom) - 1) AS id_segmento,
  degrees(st_azimuth(ST_PointN(ST_MakeLine(
    ST_PointN(geom, generate_series(1, ST_NPoints(geom) - 1)),
    ST_PointN(geom, generate_series(2, ST_NPoints(geom)))
  ), generate_series(1, ST_NPoints(ST_MakeLine(
    ST_PointN(geom, generate_series(1, ST_NPoints(geom) - 1)),
    ST_PointN(geom, generate_series(2, ST_NPoints(geom)))
  ))-1)),ST_PointN(ST_MakeLine(
    ST_PointN(geom, generate_series(1, ST_NPoints(geom) - 1)),
    ST_PointN(geom, generate_series(2, ST_NPoints(geom)))
  ), generate_series(2, ST_NPoints(ST_MakeLine(
    ST_PointN(geom, generate_series(1, ST_NPoints(geom) - 1)),
    ST_PointN(geom, generate_series(2, ST_NPoints(geom)))
  ))  )))) as azimuth,
  ST_MakeLine(
    ST_PointN(geom, generate_series(1, ST_NPoints(geom) - 1)),
    ST_PointN(geom, generate_series(2, ST_NPoints(geom)))
  ) as geom
FROM anillos
),
perpendicular as (
select 
-- analisis de perpendicular para calcular la orientacion de cada muro
st_makeline(st_centroid(geom), st_transform(st_asewkt(ST_Project(st_centroid(st_transform(geom,4326)::geography), 0.2 , radians(azimuth-90))::geometry),32719)) 
as geom
	from segmentos
),
orientation as (
select 
--id_segmento,
-- calcular la orientacion de cada muro
round(degrees(st_azimuth(st_startpoint(geom),st_endpoint(geom)))::numeric,2) as face,
geom
from perpendicular
),
data as (select distinct  
c.predio as  predios ,
c.codigo,
c.geom,
(case
    when p.face >= 0 and p.face < 67.5 then 'N'
    when p.face >= 67.5 and p.face < 157.5 then 'E'
    when p.face >= 157.5 and p.face < 247.5 then 'S'
    when p.face >= 247.5 and p.face < 337.5 then 'O'
    when p.face >= 337.5 and p.face <=360 then 'N'
end ) as lindero 
from orientation p join colindantes c on st_intersects(p.geom,c.geom))
select array_to_string(array_agg(predios),',') as predios ,lindero from data group by lindero'''.format(codigo)

        r = self.driver.read(sql)
        norte,sur,este,oeste = ['Sin Datos''','Sin Datos''','Sin Datos''','Sin Datos''']
        for data in r:
            if data['lindero'] == 'N': norte = data['predios']
            if data['lindero'] == 'E': este = data['predios']
            if data['lindero'] == 'S': sur = data['predios']
            if data['lindero'] == 'O': oeste = data['predios']

        return norte,sur,este,oeste
        
        
    def mostrar_layout(self):
    
        
        QgsProject.instance().removeAllMapLayers()
        
        list_widget = self.dlg_layout.list_bbdd
        
        current = list_widget.currentItem()
        
        
        #Obtengo el texto del QListWidgetItem
        list_widget_name = current.text()
        list_widget_name_ref = ""
        
        for asa in range(len(list_widget_name)):
            ran = len(list_widget_name) -1
            if list_widget_name[asa] == " ":
                ran = asa
                break
        
        # print()
        list_widget_name_ref = list_widget_name[0:ran]
        
        exp = f''' "codigo" = '{list_widget_name_ref}'  '''
        
        params = self.driver.params 
        uri = QgsDataSourceUri()
        uri.setConnection(params['host'],params['port'],params['dbname'],params['user'],params['password'])
        sql = f''' select * from catastro.terrenosvista19  where codigo = '{list_widget_name_ref}' '''
        uri.setDataSource('',f'({sql})','geom','','id')
        layer_terreno = QgsVectorLayer(uri.uri(False),f'terreno-{list_widget_name_ref}','postgres')
        # QgsProject.instance().addMapLayer(layer_terreno)
        
        layer_terreno.updateExtents()


        layer_terreno.loadNamedStyle(self.plugin_dir + r'\estilos\layer_terreno.qml')
        layer_terreno.triggerRepaint()

        
        uri = QgsDataSourceUri()
        uri.setConnection(params['host'],params['port'],params['dbname'],params['user'],params['password'])
        sql = f''' select id,numbloque,plantas,anyo,st_area(geom) area, geom from catastro.construccionesvista19  where codigo = '{list_widget_name_ref}' '''
        uri.setDataSource('',f'({sql})','geom','','id')
        layer_construcciones = QgsVectorLayer(uri.uri(False),'layer_construcciones','postgres')
        layer_construcciones.loadNamedStyle(self.plugin_dir + r'\estilos\layer_construcciones.qml')
        
        area_c1 = area_c2 = area_c3 = area_c4 = area_c5 = area_c6 = 0
        areas_construcciones = {'area_c1' : 0 , 'area_c2' : 0, 'area_c3' : 0 , 'area_c4' : 0 , 'area_c5' : 0, 'area_c6' : 0}
        c_total = 0

        data_construccion = {f['numbloque'] : round(f['area'],2) for f in list(layer_construcciones.getFeatures())}
        i = 1
        for k in areas_construcciones:
            try:
                areas_construcciones[k] = data_construccion[i]
                i += 1
            except KeyError:
                areas_construcciones[k] = 0
 
    
        c_total = round(sum(areas_construcciones.values()),2)
        
        layer_construcciones.triggerRepaint()
        
        # Primero, obtener los datos del terreno
        params = self.driver.params 
        uri = QgsDataSourceUri()
        uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
        sql = f''' select * from catastro.terrenosvista19 where codigo = '{list_widget_name_ref}' '''
        uri.setDataSource('', f'({sql})', 'geom', '', 'id')
        layer_terreno = QgsVectorLayer(uri.uri(False), f'terreno-{list_widget_name_ref}', 'postgres')

        # Cargar estilo para la capa de terreno
        layer_terreno.loadNamedStyle(self.plugin_dir + r'\estilos\layer_terreno.qml')

        # Verificar que la capa es válida
        if not layer_terreno.isValid() or layer_terreno.featureCount() == 0:
            self.driver.showMessage(f"No se pudo cargar el terreno con código: {list_widget_name_ref}", 2, 5)
            return

        # Obtener la feature antes de utilizarla
        feature_terreno = next(layer_terreno.getFeatures())

        # Calcular el ancho de calle utilizando el método mejorado
        ancho_calle = self.calcular_ancho_calle_mejorado(feature_terreno, list_widget_name_ref)

        # Ahora sí se puede usar feature_terreno para crear otras capas
        uri = QgsDataSourceUri()
        uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])

        # Consulta SQL para obtener ejes viales cercanos usando el ancho calculado
        sql = f'''
        SELECT 
            ev.id, 
            ev.nombre, 
            ev.geom,
            {ancho_calle} AS ancho_calle
        FROM 
            catastro.ejevias ev
        WHERE 
            ST_DWithin(
                ev.geom, 
                (SELECT geom FROM catastro.terrenos19 WHERE codigo = '{list_widget_name_ref}'),
                30
            )
        '''

        uri.setDataSource('', f'({sql})', 'geom', '', 'id')
        layerEjevias = QgsVectorLayer(uri.uri(False), list_widget_name_ref + '_EjeVias', "postgres")

        # Cargar estilo para la capa de ejes viales
        layerEjevias.loadNamedStyle(self.plugin_dir + r'\estilos\layer_ejevia.qml')

        # Verificar si se cargó correctamente el estilo, si no, aplicar respaldo
        if not layerEjevias.renderer():
            print("⚠️ Error al cargar estilo de ejes viales - aplicando estilo de respaldo")
            
            # Aplicar estilo manualmente como respaldo
            # [Código del estilo de respaldo...]

        # Refrescar la representación
        layerEjevias.triggerRepaint()
        
        uri = QgsDataSourceUri()
        uri.setConnection(params['host'],params['port'],params['dbname'],params['user'],params['password'])
        sql = f''' select n.* from catastro.terrenosvista19 n, catastro.terrenosvista19 p
        where st_touches(n.geom,p.geom) 
        and p.codigo = '{list_widget_name_ref}'
        and n.codigo != '{list_widget_name_ref}' '''
        uri.setDataSource('',f'({sql})','geom','','id')
        layer_todos_terrenos19 = QgsVectorLayer(uri.uri(False),'layer_todos_terrenos19','postgres')

        layer_todos_terrenos19.loadNamedStyle(self.plugin_dir + r'\estilos\todos_terrenos.qml')
        layer_todos_terrenos19.triggerRepaint()



        path = self.ortofoto
        rlayer = QgsRasterLayer(path, 'Ortofoto') 

        # QgsProject.instance().addMapLayer(rlayer)
        #* working well

        feature_terreno = [e for e in layer_terreno.getFeatures()][0]

        # Cálculo y guardado del geocódigo
        try:
            sql_centroid = f"""
            SELECT ST_X(ST_Centroid(geom)) as x, 
                ST_Y(ST_Centroid(geom)) as y
            FROM catastro.terrenosvista19  
            WHERE codigo = '{list_widget_name_ref}'
            """
            centroid_result = self.driver.read(sql_centroid, multi=False)
            
            if centroid_result:
                x = centroid_result['x']
                y = centroid_result['y']
                
                # Zona UTM Bolivia
                zona_utm = 19
                
                # Cálculo cuadrícula 1000x1000
                cuad_1000_x = int(x // 1000)
                cuad_1000_y = int(y // 1000)
                
                # Norte o sur
                y_dentro_1000 = y % 1000
                hoja = "N" if y_dentro_1000 >= 500 else "S"
                
                # Cálculo cuadrícula 100x100
                x_dentro_1000 = x % 1000
                y_dentro_500 = y_dentro_1000 % 500
                cuad_100_x = int(x_dentro_1000 // 100)
                cuad_100_y = int(y_dentro_500 // 100)
                num_cuadricula = cuad_100_x + (cuad_100_y * 10) + 1
                
                # Cálculo cuadrícula 20x20
                x_dentro_100 = x % 100
                y_dentro_100 = y % 100
                cuad_20_x = int(x_dentro_100 // 20)
                cuad_20_y = int(y_dentro_100 // 20)
                num_cuadricula_20 = cuad_20_x + (cuad_20_y * 5) + 1
                
                # Generar geocódigo
                geocodigo = f"{zona_utm}{cuad_1000_x:03d}{cuad_1000_y:03d}{hoja}{num_cuadricula:02d}{num_cuadricula_20:02d}"

                # Guardar en base de datos
                sql_update = f"""
                UPDATE catastro.terrenos19 
                SET geocod = '{geocodigo}'
                WHERE codigo = '{list_widget_name_ref}'
                """
                self.driver.update(sql_update)
        except Exception as ex:
            self.driver.showMessage(f"Error al calcular geocódigo: {str(ex)}", 1, 15)
            
        sql_get_geocod = f"""
        SELECT geocod FROM catastro.terrenos19 
        WHERE codigo = '{list_widget_name_ref}'
        """
        geocod_result = self.driver.read(sql_get_geocod, multi=False)
        geocod_value = geocod_result['geocod'] if geocod_result and geocod_result['geocod'] else 'Sin datos'    


        uri = QgsDataSourceUri()
        uri.setConnection(params['host'],params['port'],params['dbname'],params['user'],params['password'])
        sql = f''' select (st_dumppoints(geom)).path[3] as id,
        'V'||(st_dumppoints(geom)).path[3] as nombre,
        st_x((st_dumppoints(geom)).geom) este,
        st_y((st_dumppoints(geom)).geom) norte, 
        (st_dumppoints(geom)).geom 
        from catastro.terrenos19 where codigo = '{list_widget_name_ref}' '''
        uri.setDataSource('',f'({sql})','geom','','id')
        vertexLayer = QgsVectorLayer(uri.uri(False), feature_terreno["codigo"] + '_Vertices', "postgres")

        coordenadas = []
        for f in vertexLayer.getFeatures(): 
            geom = f.geometry().asPoint()
            coordenadas.append(geom.x())
            coordenadas.append(geom.y())

        dataTable = []
        for f in vertexLayer.getFeatures(): 
            geom = f.geometry().asPoint()
            l = []
            l.append(f['nombre'])
            l.append(str(round(geom.x(),2)))
            l.append(str(round(geom.y(),2)))
            dataTable.append(l)
        # print(data)
        

        vertexLayer.loadNamedStyle(self.plugin_dir + r'\estilos\layer_vertex.qml')
        vertexLayer.triggerRepaint()

        uri = QgsDataSourceUri()
        uri.setConnection(params['host'],params['port'],params['dbname'],params['user'],params['password'])
        sql = f''' select row_number () over () as id, round(cast(st_length(ST_MakeLine(sp,ep))as numeric) ,2) as distancia ,ST_MakeLine(sp,ep) as geom
        FROM
        -- extract the endpoints for every 2-point line segment for each linestring
        (SELECT
            ST_PointN(geom, generate_series(1, ST_NPoints(geom)-1)) as sp,
            ST_PointN(geom, generate_series(2, ST_NPoints(geom)  )) as ep
            FROM
            -- extract the individual linestrings
            (SELECT (ST_Dump(ST_Boundary(geom))).geom
            FROM catastro.terrenos19 where codigo = '{list_widget_name_ref}'
            ) AS linestrings
            ) AS segments  '''
        uri.setDataSource('',f'({sql})','geom','','id')
        layerLineas = QgsVectorLayer(uri.uri(False), feature_terreno["codigo"] + '_Lineas', "postgres")

        layerLineas.loadNamedStyle(self.plugin_dir + r'\estilos\lineas_medidas.qml')
        layerLineas.triggerRepaint()
        
        
        uri = QgsDataSourceUri()
        uri.setConnection(params['host'],params['port'],params['dbname'],params['user'],params['password'])
        sql = f''' select * from catastro.terrenosvista19  where codigo = '{list_widget_name_ref}' '''
        uri.setDataSource('',f'({sql})','geom','','id')
        layerLineasUbicacion = QgsVectorLayer(uri.uri(False), feature_terreno["codigo"] + '_LineasUbicacion','postgres')   
        layerLineasUbicacion.loadNamedStyle(self.plugin_dir + r'\estilos\layer_ubicacion.qml')
        layerLineasUbicacion.triggerRepaint()
        # print(layerLineasUbicacion.isValid())
        # # QgsProject.instance().addMapLayer(layerLineasUbicacion)

        
        import psycopg2

        # Asumiendo que ya tiene los parámetros de conexión definidos en 'params'
        # y que 'list_widget_name_ref' contiene el código del terreno que está procesando

        # Configurar la conexión a la base de datos
        connection = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            dbname=params['dbname'],
            user=params['user'],
            password=params['password']
        )

        # Crear un cursor
        cursor = connection.cursor()

        # SQL para calcular todas las distancias y sus puntos de inicio y fin
        sql = f'''
        SELECT 
            round(cast(st_length(ST_MakeLine(sp,ep)) as numeric), 2) as distancia,
            ST_AsText(sp) as start_point,
            ST_AsText(ep) as end_point
        FROM (
            SELECT
                ST_PointN(geom, generate_series(1, ST_NPoints(geom)-1)) as sp,
                ST_PointN(geom, generate_series(2, ST_NPoints(geom))) as ep
            FROM (
                SELECT (ST_Dump(ST_Boundary(geom))).geom
                FROM catastro.terrenos19 
                WHERE codigo = '{list_widget_name_ref}'
            ) AS linestrings
        ) AS segments
        ORDER BY distancia DESC;
        '''

        # Ejecutar la consulta
        cursor.execute(sql)
        results = cursor.fetchall()

        print(f"Distancias calculadas para el terreno {list_widget_name_ref}:")
        for i, (distancia, start, end) in enumerate(results, 1):
            print(f"Lado {i}: {distancia} metros, desde {start} hasta {end}")

        if len(results) >= 2:
            # El fondo es el lado más largo (primer resultado)
            fondo = results[0][0]
            
            # El frente es el tercer lado más largo (que en este caso es uno de los más cortos)
            frente = results[2][0] if len(results) > 2 else results[-1][0]

            print(f"\nActualizado: Frente = {frente:.2f}, Fondo = {fondo:.2f}")

            # SQL para actualizar la base de datos
            update_sql = f'''
            UPDATE catastro.terrenos19
            SET frente = ROUND({frente}::numeric, 2), fondo = ROUND({fondo}::numeric, 2)
            WHERE codigo = '{list_widget_name_ref}';
            '''

            # Ejecutar la actualización
            cursor.execute(update_sql)
            connection.commit()

            print(f"Base de datos actualizada para el terreno {list_widget_name_ref}")

        # Cerrar el cursor y la conexión
        cursor.close()
        connection.close()

        project = QgsProject.instance()         
        
        manager = project.layoutManager()       
        
        layout = QgsPrintLayout(project)        
        
        layoutName = "PLANO DE LOTE"
        
        layouts_list = manager.printLayouts()

        for layout in layouts_list:
            if layout.name() == layoutName:
                manager.removeLayout(layout)
                
        
        layout = QgsPrintLayout(project)
        
        layout.initializeDefaults()                 
        
        layout.setName(layoutName)
        
        manager.addLayout(layout)

        pc = layout.pageCollection()
        pc.page(0).setPageSize(QgsLayoutSize(210, 333, QgsUnitTypes.LayoutMillimeters))
        
       
        tmpfile = self.plugin_dir + "/riberaltalayout2_2.qpt"
   

        with open(tmpfile) as f:
            template_content = f.read()
        
        doc = QDomDocument()
        doc.setContent(template_content)
        
        
        items, ok = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)
        
        layout.itemById('id_names').setText(str(feature_terreno["nombre"]) + " " + str(feature_terreno["apellidos"]))
        layout.itemById('id_manzano').setText(str(feature_terreno["manzano"]))
        layout.itemById('id_predio').setText(str(feature_terreno["predio"]))
        layout.itemById('id_predio2').setText(str(feature_terreno["predio"]))  # Nuevo ID para el duplicado
        layout.itemById('id_direccion').setText(str(feature_terreno["direccion"]))
        layout.itemById('id_zona').setText(str(feature_terreno["barrio"]))
        layout.itemById('id_documento').setText(str(feature_terreno["documento"]))
        layout.itemById('id_codigo').setText(str(feature_terreno["codigo"]))
        layout.itemById('id_distrito').setText(str(feature_terreno["distrito"]))
        layout.itemById('id_geocod').setText(str(geocod_value))  # Usar el valor actualizado
        
        codigo_referencia = feature_terreno["codigo"]
        norte, sur, este, oeste = self.obtener_calles_y_colindantes(codigo_referencia)
        layout.itemById('colindante_norte').setText(str(norte) )
        layout.itemById('colindante_sur').setText(str(sur) )
        layout.itemById('colindante_este').setText(str(este) )
        layout.itemById('colindante_oeste').setText(str(oeste) )
        
        
        try:
            suptest2 = float(feature_terreno["suptest"])
           
        except:
            suptest2 = 0

        layout.itemById('id_suptest').setText('{} m²'.format(str(round(suptest2,2))))
        
        
        sup = 0
        if feature_terreno["superficie"]:
            sup = feature_terreno["superficie"]
        sup2 = round(sup, 2)
        layout.itemById('id_superficie').setText('{} m²'.format(str(sup2)))

        resta = suptest2 - float(feature_terreno["superficie"])
        resta2 = round(resta,2)
        layout.itemById('id_diferencia').setText('{} m²'.format(str(resta2)))
        
        sup_total = sup + resta

        layout.itemById('id_suptotal').setText('{} m²'.format(str(sup_total)))
        layout.itemById('id_c1').setText('{} m²'.format(str(areas_construcciones['area_c1'])))
        layout.itemById('id_c2').setText('{} m²'.format(str(areas_construcciones['area_c2'])))
        layout.itemById('id_c3').setText('{} m²'.format(str(areas_construcciones['area_c3'])))
        layout.itemById('id_c4').setText('{} m²'.format(str(areas_construcciones['area_c4'])))
        layout.itemById('id_c5').setText('{} m²'.format(str(areas_construcciones['area_c5'])))
        layout.itemById('id_c6').setText('{} m²'.format(str(areas_construcciones['area_c6'])))
        layout.itemById('id_ctotal').setText('{} m²'.format(str(c_total)))

        
        now = datetime.now()
        
        layout.itemById('id_date').setText("{}/{}/{}".format(now.day, now.month, now.year))

        # print(layout.itemById('id_vertex'))
        table = QgsLayoutItemTextTable(layout)
        layout.addMultiFrame(table)

        # Add columns       
        cols = [QgsLayoutTableColumn(),QgsLayoutTableColumn(),QgsLayoutTableColumn()]
        cols[0].setHeading("heading 0")
        cols[1].setHeading("heading 1")
        cols[2].setHeading("heading 2")
        table.setColumns(cols)

        # Add only 1 row
        for e in dataTable:
            table.addRow(e)

        table.setGridStrokeWidth(0.3) # 0.1 mm
        content_text_format = QgsTextFormat()
        content_text_format.setSize(6)
        table.setContentTextFormat(content_text_format)
        header_text_format = QgsTextFormat()
        header_text_format.setSize(6)
        table.setHeaderTextFormat(header_text_format)

        # Base class for frame items, which form a layout multiframe item.
        frame = QgsLayoutFrame(layout, table)
        frame.setMinimumSize(QgsLayoutSize(36, 79))
        frame.attemptResize(QgsLayoutSize(36, 79), False)
        frame.attemptMove(QgsLayoutPoint(6, 249, QgsUnitTypes.LayoutMillimeters))
        table.addFrame(frame)
        data = [1,2,3]
        fields = ['Nombre','Este','Norte']
        cols = [QgsLayoutTableColumn(), QgsLayoutTableColumn(), QgsLayoutTableColumn()]
        for n in range(0, len(fields)):
            cols[n].setHeading(fields[n])
        table.setColumns(cols)
            
        project = QgsProject.instance()
    
        mapas = []

        for i in items: 
            if i.type() == 65639:
                mapas.append(i)
                       
        mapa1 = mapas[0]
        mapa2 = mapas[1]
        
        nombre = ""
        
               
        if nombre == "":
            QgsProject.instance().addMapLayer(rlayer)
        
        QgsProject.instance().addMapLayer(layer_terreno)
        QgsProject.instance().addMapLayer(layer_todos_terrenos19)
        QgsProject.instance().addMapLayer(layerLineasUbicacion)        
        QgsProject.instance().addMapLayer(layerEjevias)
        QgsProject.instance().addMapLayer(vertexLayer)
        QgsProject.instance().addMapLayer(layerLineas)

 
        # if feature_construccion != []: 
        QgsProject.instance().addMapLayer(layer_construcciones)
       
        
        map_settings = iface.mapCanvas().mapSettings() 
        
                
        mapa1.setRect(20, 20, 20, 20)
        
        ms1 = QgsMapSettings()
        ms1.setLayers([layer_terreno])
        
        # if feature_construccion != []: 
            # mapa1.setLayers([layerConstruccion, vertexLayer, layer, layerLineas])
        # else:
        mapa1.setLayers([vertexLayer,layer_construcciones,layer_terreno,layerLineas,layer_todos_terrenos19,layerEjevias])
        
        rect1 = QgsRectangle(ms1.fullExtent())
        rect1.scale(5)
        ms1.setExtent(rect1)
        mapa1.setExtent(rect1)
        # mapa1.setScale(2000)
        mapa1.setBackgroundColor(QColor(255, 0, 0, 0))
        mapa1.attemptMove(QgsLayoutPoint(10,62,QgsUnitTypes.LayoutMillimeters))
        mapa1.attemptResize(QgsLayoutSize(190, 135, QgsUnitTypes.LayoutMillimeters))
        
        mapa2.setRect(20, 20, 20, 20) 
        ms2 = QgsMapSettings()
        ms2.setLayers([layer_terreno])
        mapa2.setLayers([layerLineasUbicacion,layer_todos_terrenos19,layerEjevias,rlayer])
        
        rect2 = QgsRectangle(ms2.fullExtent())
        rect2.scale(5)
        ms2.setExtent(rect2)
        mapa2.setExtent(rect2)
        
        mapa2.attemptMove(QgsLayoutPoint(100, 210, QgsUnitTypes.LayoutMillimeters))
        mapa2.attemptResize(QgsLayoutSize(104, 101, QgsUnitTypes.LayoutMillimeters))


        iface.openLayoutDesigner(layout)
        exporter = QgsLayoutExporter(layout)    
        exporter.exportToPdf(self.plugin_dir + "/Layout.pdf", QgsLayoutExporter.PdfExportSettings()) 


        iface.mapCanvas().setExtent(layer_terreno.extent()) 
                    
        
    ############################################################################################################################################
    ############################################################QUINTO BOTON PRIMER CERTIFICADO#################################################
    ############################################################################################################################################ 
    
    
    lista_terreno_informe = ""
    
    def cargar_tablabbdd2(self):
    
      
            
        list_widget = self.dlg_informe.list_bbdd
        
        for i in range(list_widget.count()):
            list_widget.takeItem(0)
        
        r = self.driver.read('select codigo, nombre, apellidos, documento from catastro.terrenosvista19')
        # print(r)
        
        
        lista = []
                
        for item in r:

            if item["nombre"] or item["apellidos"]:

                lista.append(str(item["codigo"]) + "   " + str(item["nombre"])  + "   " + str(item["apellidos"]))
            else:
                lista.append(str(item["codigo"]))
       
        list_widget.addItems(lista)
        
        self.lista_terreno_informe = r
        
       
          
    
    def listar_layer_informe_busca_ref(self):
        
        list_widget = self.dlg_informe.list_bbdd
            
        
            
        text_busqueda  = self.dlg_select_terreno_informe_busca_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText()
                  
        r = self.driver.read(f''' select codigo, nombre, apellidos, documento from catastro.terrenosvista19 where codigo ilike '%{valor_busqueda}%' ''')

        if len(r) > 0 :
            for i in range(list_widget.count()):
                list_widget.takeItem(0)
            lista = [str(item["codigo"]) + "   " + str(item["nombre"]) + " " + str(item["apellidos"]) for item in r]
            list_widget.addItems(lista)
        else: 
            self.driver.showMessage('No existen registros con este Codigo Catastral .',1,15)
        
            
    
    def listar_layer_informe_busca_nombre(self):
    
        list_widget = self.dlg_informe.list_bbdd
                  
        text_busqueda  = self.dlg_select_terreno_informe_busca_nombre.text_titular
        valor_busqueda = text_busqueda.toPlainText()
            

        try: 
            q = ''
            for e in valor_busqueda.split(): 
                q  = q + '%' + e + '% '

            sql = f''' select codigo, nombre, apellidos, documento from catastro.terrenosvista19 where nombre || ' ' || apellidos ilike '{q[:-1]}' '''
            r = self.driver.read(sql)
            if len(r) > 0:
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                lista = [str(item["codigo"]) + "   " + str(item["nombre"]) + " " + str(item["apellidos"]) for item in r]
                list_widget.addItems(lista)
            else: 
                self.driver.showMessage('No existen registros con los valores buscados.',1,15)
                    

        except Exception as ex: 
            print(ex)
        
    def obtener_calles_y_colindantes(self, codigo_referencia):
        """
        Versión con mejor limpieza de nombres de calles
        """
        try:
            # Consulta para calles (sin cambios)
            sql_calles = f"""
                WITH terreno_ref AS (
                    SELECT 
                        ST_SetSRID(geom, 32719) as geom,
                        ST_YMax(ST_SetSRID(geom, 32719)) as ymax,
                        ST_YMin(ST_SetSRID(geom, 32719)) as ymin,
                        ST_XMax(ST_SetSRID(geom, 32719)) as xmax,
                        ST_XMin(ST_SetSRID(geom, 32719)) as xmin,
                        ST_Centroid(ST_SetSRID(geom, 32719)) as centro
                    FROM catastro.terrenosvista19 
                    WHERE codigo = '{codigo_referencia}'
                )
                SELECT 
                    CASE
                        WHEN LOWER(ev.nombre) LIKE 'avenida%' THEN 
                            'AV. ' || TRIM(REPLACE(REPLACE(REPLACE(UPPER(ev.nombre), 'AVENIDA', ''), 'AV.', ''), 'AV', ''))
                        ELSE 
                            'C. ' || TRIM(REPLACE(REPLACE(UPPER(ev.nombre), 'CALLE', ''), 'C.', ''))
                    END as nombre_calle,
                    CASE
                        WHEN ST_Y(ST_ClosestPoint(ST_SetSRID(ev.geom, 32719), t.geom)) > t.ymax AND
                            ST_X(ST_ClosestPoint(ST_SetSRID(ev.geom, 32719), t.geom)) BETWEEN (t.xmin - 10) AND (t.xmax + 10)
                        THEN 'NORTE'
                        WHEN ST_Y(ST_ClosestPoint(ST_SetSRID(ev.geom, 32719), t.geom)) < t.ymin AND
                            ST_X(ST_ClosestPoint(ST_SetSRID(ev.geom, 32719), t.geom)) BETWEEN (t.xmin - 10) AND (t.xmax + 10)
                        THEN 'SUR'
                        WHEN ST_X(ST_ClosestPoint(ST_SetSRID(ev.geom, 32719), t.geom)) > t.xmax AND
                            ST_Y(ST_ClosestPoint(ST_SetSRID(ev.geom, 32719), t.geom)) BETWEEN (t.ymin - 10) AND (t.ymax + 10)
                        THEN 'ESTE'
                        ELSE 'OESTE'
                    END as direccion
                FROM catastro.ejevias ev, terreno_ref t
                WHERE ST_DWithin(ST_SetSRID(ev.geom, 32719), t.geom, 20)
                AND ev.nombre IS NOT NULL;
            """

            # Modificación de la consulta para colindantes (añadimos nombre y apellidos)
            sql_colindantes = f"""
                WITH terreno_ref AS (
                    SELECT 
                        ST_SetSRID(geom, 32719) as geom,
                        ST_YMax(ST_SetSRID(geom, 32719)) as ymax,
                        ST_YMin(ST_SetSRID(geom, 32719)) as ymin,
                        ST_XMax(ST_SetSRID(geom, 32719)) as xmax,
                        ST_XMin(ST_SetSRID(geom, 32719)) as xmin,
                        ST_Centroid(ST_SetSRID(geom, 32719)) as centro
                    FROM catastro.terrenosvista19 
                    WHERE codigo = '{codigo_referencia}'
                ),
                colindantes_info AS (
                    SELECT 
                        split_part(n.codigo, '.', 5) as num_predio,
                        n.nombre,
                        n.apellidos,
                        CASE
                            WHEN ST_Touches(ST_SetSRID(n.geom, 32719), t.geom) AND
                                ST_X(ST_Centroid(n.geom)) < ST_X(t.centro) AND
                                ST_Y(ST_Centroid(n.geom)) BETWEEN (ST_YMin(t.geom) - 2) AND (ST_YMax(t.geom) + 2)
                            THEN 'OESTE'
                            WHEN ST_Y(ST_Centroid(n.geom)) > ST_YMax(t.geom) THEN 'NORTE'
                            WHEN ST_Y(ST_Centroid(n.geom)) < ST_YMin(t.geom) THEN 'SUR'
                            WHEN ST_X(ST_Centroid(n.geom)) > ST_XMax(t.geom) THEN 'ESTE'
                            WHEN ST_X(ST_Centroid(n.geom)) < ST_XMin(t.geom) THEN 'OESTE'
                        END as direccion,
                        ST_Distance(ST_Centroid(n.geom), t.centro) as dist_centro
                    FROM catastro.terrenosvista19 n, terreno_ref t
                    WHERE ST_Touches(ST_SetSRID(n.geom, 32719), t.geom)
                    AND n.codigo != '{codigo_referencia}'
                )
                SELECT 
                    direccion,
                    string_agg(
                        CASE 
                            WHEN nombre IS NOT NULL AND apellidos IS NOT NULL THEN 
                                TRIM(nombre) || ' ' || TRIM(apellidos)
                            WHEN nombre IS NOT NULL THEN 
                                TRIM(nombre)
                            WHEN apellidos IS NOT NULL THEN 
                                TRIM(apellidos)
                            ELSE 
                                'Predio ' || num_predio
                        END, 
                        ', ' ORDER BY dist_centro
                    ) as predios
                FROM colindantes_info
                WHERE direccion IS NOT NULL
                GROUP BY direccion;
            """

            # El resto del método queda exactamente igual
            calles_result = self.driver.read(sql_calles)
            colindantes_result = self.driver.read(sql_colindantes)

            print("\nCalles encontradas:")
            print(calles_result)
            print("\nColindantes encontrados:")
            print(colindantes_result)

            # Inicializar diccionario
            info_direcciones = {
                'NORTE': 'Sin datos',
                'SUR': 'Sin datos',
                'ESTE': 'Sin datos',
                'OESTE': 'Sin datos'
            }

            # Procesar calles
            if calles_result:
                for calle in calles_result:
                    if calle['direccion'] and calle['nombre_calle']:
                        nombre_limpio = calle['nombre_calle'].strip()
                        # Eliminar múltiples espacios
                        while "  " in nombre_limpio:
                            nombre_limpio = nombre_limpio.replace("  ", " ")
                        info_direcciones[calle['direccion']] = nombre_limpio

            # Procesar colindantes
            if colindantes_result:
                for col in colindantes_result:
                    if col['direccion']:
                        direccion = col['direccion']
                        if info_direcciones[direccion] == 'Sin datos':
                            info_direcciones[direccion] = col['predios'].strip()

            print("\nInformación final por dirección:")
            for dir, info in info_direcciones.items():
                print(f"{dir}: {info}")

            return (
                info_direcciones['NORTE'],
                info_direcciones['SUR'],
                info_direcciones['ESTE'],
                info_direcciones['OESTE']
            )

        except Exception as ex:
            print(f"Error completo: {str(ex)}")
            self.driver.showMessage(f'Error: {str(ex)}', 1, 15)
            return ('Error', 'Error', 'Error', 'Error')   
         
        
        
    def mostrar_informe(self):
        try:
            # Limpiar todas las capas existentes en QGIS
            QgsProject.instance().removeAllMapLayers()
            
            list_widget = self.dlg_informe.list_bbdd
            
            current = list_widget.currentItem()
            if not current:
                self.driver.showMessage('Seleccione un terreno', 1, 15)
                return
            
            #Obtengo el texto del QListWidgetItem
            list_widget_name = current.text()
            list_widget_name_ref = ""
            
            for asa in range(len(list_widget_name)):
                if list_widget_name[asa] == " ":
                    ran = asa
                    break
            
            list_widget_name_ref = list_widget_name[0:ran]

            params = self.driver.params 
            norte, sur, este, oeste = self.obtener_calles_y_colindantes(list_widget_name_ref)
            
            # Crear capa de terreno
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f''' select
            t.id,
            t.codigo,
            t.geocod,
            t.folio_ddrr,
            t.folio_ddrr matricula_ddrr,
            n_test,
            fecha_test,
            t.zona,
            t.barrio,
            t.direccion,
            t.manzano,
            t.predio, 
            t.suptest,
            t.superficie,
            t.nombre,
            t.apellidos,
            t.frente,
            t.fondo,
            t.perimetro,
            (case when t.energia then 'Si' else 'No' end) luz,
                    (case when t.agua then 'Si' else 'No' end) agua,
                    (case when t.alcantarillado then 'Si' else 'No' end) alcantarillado,
            
            t.geom 
            from catastro.terrenosvista19 t 
            left join (select codigo, sum(st_area(geom)) area, max(tipo) tipo, min(anyo) antiguedad 
                    from catastro.construccionesvista19 group by codigo) as c on c.codigo = t.codigo
            where t.codigo = '{list_widget_name_ref}' '''
            
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            layer_terreno = QgsVectorLayer(uri.uri(False), 'layer_terreno', 'postgres')
            
            # Verificar que la capa es válida
            if not layer_terreno.isValid():
                print("Error en la capa:", layer_terreno.dataProvider().error().summary())
                self.driver.showMessage('Error al crear capa de terreno', 1, 15)
                return
            
            layer_terreno.updateExtents()
            layer_terreno.loadNamedStyle(self.plugin_dir + r'\estilos\layer_terreno.qml')
            layer_terreno.triggerRepaint()

            # Verificar que hay features
            features = list(layer_terreno.getFeatures())
            if not features:
                print(f"No se encontraron terrenos con código: {list_widget_name_ref}")
                self.driver.showMessage('No se encontró el terreno especificado', 1, 15)
                return
            
            feature_terreno = features[0]
            
            # Código para obtener co-titulares
            try:
                # Obtenemos el ID del titular principal del terreno
                sql_titular_id = f"""
                SELECT 
                    titular
                FROM 
                    catastro.terrenos19
                WHERE 
                    codigo = '{feature_terreno["codigo"]}'
                LIMIT 1
                """
                
                titular_result = self.driver.read(sql_titular_id)
                
                cotitulares_nombres = []
                
                if titular_result and len(titular_result) > 0 and titular_result[0]['titular'] is not None:
                    titular_id = titular_result[0]['titular']
                    
                    # Ahora buscamos los co-titulares relacionados con este titular
                    sql_cotitulares = f"""
                    SELECT 
                        ct.nombre, 
                        ct.apellidos, 
                        ct.documento
                    FROM 
                        catastro.co_titular ct
                    WHERE 
                        ct.titular_id = {titular_id}
                    ORDER BY 
                        ct.nombre, ct.apellidos
                    """
                    
                    cotitulares_result = self.driver.read(sql_cotitulares)
                    
                    if cotitulares_result:
                        for cotitular in cotitulares_result:
                            nombre = cotitular['nombre'] if cotitular['nombre'] else ""
                            apellidos = cotitular['apellidos'] if cotitular['apellidos'] else ""
                            nombre_completo = f"{nombre} {apellidos}".strip()
                            if nombre_completo:
                                cotitulares_nombres.append(nombre_completo)
                
                cotitulares_texto = ", ".join(cotitulares_nombres) if cotitulares_nombres else "No hay co-titulares"
                print(f"Co-titulares encontrados: {cotitulares_texto}")
            except Exception as ex:
                print(f"Error al obtener co-titulares: {str(ex)}")
                cotitulares_texto = "Error al obtener co-titulares"
            
            # Crear capa de líneas de medidas
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f''' select row_number () over () as id, round(cast(st_length(ST_MakeLine(sp,ep))as numeric) ,2) as distancia ,ST_MakeLine(sp,ep) as geom
            FROM
            -- extract the endpoints for every 2-point line segment for each linestring
            (SELECT
                ST_PointN(geom, generate_series(1, ST_NPoints(geom)-1)) as sp,
                ST_PointN(geom, generate_series(2, ST_NPoints(geom)  )) as ep
                FROM
                -- extract the individual linestrings
                (SELECT (ST_Dump(ST_Boundary(geom))).geom
                FROM catastro.terrenos19 where codigo = '{list_widget_name_ref}'
                ) AS linestrings
                ) AS segments  '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            layerLineas = QgsVectorLayer(uri.uri(False), f'lineas_{list_widget_name_ref}', "postgres")
            layerLineas.loadNamedStyle(self.plugin_dir + r'\estilos\lineas_medidas.qml')
            layerLineas.triggerRepaint()
            
            # Crear capa de ubicación
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql_ubicacion = f''' select
                    row_number() OVER () as uid,
                    t.id,
                    t.geom 
                    from catastro.terrenosvista19 t 
                    where t.codigo = '{list_widget_name_ref}' '''
            uri.setDataSource('', f'({sql_ubicacion})', 'geom', '', 'uid')
            layer_ubicacion = QgsVectorLayer(uri.uri(False), f'ubicacion-{feature_terreno["codigo"]}', 'postgres')
            layer_ubicacion.updateExtents()
            try:
                layer_ubicacion.loadNamedStyle(self.plugin_dir + r'\estilos\layer_ubicacion.qml')
            except Exception as e:
                print(f"Error al cargar estilo de ubicación: {str(e)}")
            layer_ubicacion.triggerRepaint()
            
            # Crear capa de colindantes
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f''' select n.* from catastro.terrenosvista19 n, catastro.terrenosvista19 p
            where st_touches(n.geom,p.geom) 
            and p.codigo = '{list_widget_name_ref}'
            and n.codigo != '{list_widget_name_ref}' '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            layer_colindantes = QgsVectorLayer(uri.uri(False), 'layer_colindantes', 'postgres')
            layer_colindantes.loadNamedStyle(self.plugin_dir + r'\estilos\todos_terrenos.qml')
            layer_colindantes.triggerRepaint()

            # Crear capa de ejes viales
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f'''select ejevias.* from catastro.ejevias
                join catastro.terrenos19 on st_intersects(st_buffer(terrenos19.geom,15),ejevias.geom)
                where terrenos19.codigo = '{list_widget_name_ref}' and st_intersects(st_buffer(terrenos19.geom,15),ejevias.geom) '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            layerEjevias = QgsVectorLayer(uri.uri(False), feature_terreno["codigo"] + '_EjeVias', "postgres")
            layerEjevias.loadNamedStyle(self.plugin_dir + r'\estilos\layer_ejevia.qml')
            layerEjevias.triggerRepaint()
            
            # Configuración para etiquetas de ejes viales
            try:
                # Crear configuración de etiquetado
                label_settings = QgsPalLayerSettings()
                label_settings.enabled = True
                label_settings.fieldName = 'nombre'  # Campo a mostrar en la etiqueta
                
                # Configurar formato del texto
                text_format = QgsTextFormat()
                text_format.setSize(8)  # Tamaño de la fuente
                text_format.setColor(QColor('blue'))  # Color del texto
                text_format.setNamedStyle('Bold')  # Estilo de la fuente
                
                # Fondo blanco para mejor legibilidad
                buffer_settings = QgsTextBufferSettings()
                buffer_settings.setEnabled(True)
                buffer_settings.setSize(0.6)
                buffer_settings.setColor(QColor('white'))
                text_format.setBuffer(buffer_settings)
                
                label_settings.setFormat(text_format)
                
                # Configurar posición
                label_settings.placement = QgsPalLayerSettings.Line
                label_settings.placementFlags = QgsPalLayerSettings.AboveLine
                
                # Aplicar etiquetado
                labeling = QgsVectorLayerSimpleLabeling(label_settings)
                layerEjevias.setLabeling(labeling)
                layerEjevias.setLabelsEnabled(True)
            except Exception as e:
                print(f"Error al configurar etiquetas de ejevias: {str(e)}")
            
            # Cargar ortofoto si existe
            try:
                ortofoto = QgsRasterLayer(self.ortofoto, 'Ortofoto')
                if ortofoto.isValid():
                    QgsProject.instance().addMapLayer(ortofoto)
            except Exception as e:
                print(f"Error al cargar ortofoto: {str(e)}")
                ortofoto = None
            
            # Crear capa de construcciones si existen
            try:
                uri = QgsDataSourceUri()
                uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
                sql_const = f''' select id, numbloque, plantas, anyo, st_area(geom) as area, geom 
                            from catastro.construccionesvista19  
                            where codigo = '{list_widget_name_ref}' '''
                uri.setDataSource('', f'({sql_const})', 'geom', '', 'id')
                layer_construcciones = QgsVectorLayer(uri.uri(False), 'layer_construcciones', 'postgres')
                layer_construcciones.loadNamedStyle(self.plugin_dir + r'\estilos\layer_construcciones.qml')
                layer_construcciones.triggerRepaint()
                QgsProject.instance().addMapLayer(layer_construcciones)
            except Exception as e:
                print(f"Error al cargar construcciones: {str(e)}")
                layer_construcciones = None
            
            # Añadir capas al proyecto en orden correcto
            if 'ortofoto' in locals() and ortofoto and ortofoto.isValid():
                QgsProject.instance().addMapLayer(ortofoto)
            
            for l in [layer_terreno, layer_colindantes, layerEjevias, layerLineas, layer_ubicacion]:
                if l and l.isValid():
                    QgsProject.instance().addMapLayer(l)

            # Crear layout
            project = QgsProject.instance()         
            manager = project.layoutManager()       
            layout = QgsPrintLayout(project)        
            layoutName = "Acta"
            
            layouts_list = manager.printLayouts()
            for layout in layouts_list:
                if layout.name() == layoutName:
                    manager.removeLayout(layout)
            
            layout = QgsPrintLayout(project)
            layout.initializeDefaults()
            layout.setName(layoutName)
            manager.addLayout(layout)
            
            # Configurar orientación de página
            pc = layout.pageCollection()
            pc.page(0).setPageSize('Legal', QgsLayoutItemPage.Orientation.Portrait)
            
            # Cargar plantilla
            tmpfile = self.plugin_dir + '/riberaltainforme1.qpt'
            with open(tmpfile) as f:
                template_content = f.read()
            
            doc = QDomDocument()
            doc.setContent(template_content)
            
            # Cargar elementos desde la plantilla
            items, ok = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)
            if not ok:
                self.driver.showMessage('Error al cargar la plantilla', 1, 15)
                return
            
            # Extraer información del código
            now = datetime.now()
            codigo = feature_terreno["codigo"].split('.')
            predio = codigo[-1]
            manzano = codigo[-2]
            distrito = codigo[-4] if len(codigo) > 3 else ""
            
            # Configurar mapa de ubicación
            mapa_ubicacion = layout.itemById('id_mapa_ubicacion')
            if mapa_ubicacion and isinstance(mapa_ubicacion, QgsLayoutItemMap):
                # Configurar las capas en el orden correcto
                ms2 = QgsMapSettings()
                ms2.setLayers([layer_ubicacion])
                
                # Configurar las capas
                capas_mapa = []
                if 'layer_construcciones' in locals() and layer_construcciones and layer_construcciones.isValid():
                    capas_mapa.append(layer_construcciones)
                capas_mapa.append(layer_terreno)
                capas_mapa.append(layerEjevias)
                capas_mapa.append(layer_ubicacion)
                if 'ortofoto' in locals() and ortofoto and ortofoto.isValid():
                    capas_mapa.append(ortofoto)
                
                # Establecer capas y extensión
                mapa_ubicacion.setLayers(capas_mapa)
                rect2 = QgsRectangle(ms2.fullExtent())
                rect2.scale(5)
                mapa_ubicacion.setExtent(rect2)
                mapa_ubicacion.attemptResize(QgsLayoutSize(95, 80, QgsUnitTypes.LayoutMillimeters))
                mapa_ubicacion.refresh()
            
            # Configurar mapa principal
            mapa = layout.itemById('mapa_1')
            if mapa and isinstance(mapa, QgsLayoutItemMap):
                mapa_settings = QgsMapSettings()
                mapa.setLayers([layer_terreno, layer_construcciones, layer_colindantes, layerLineas])
                mapa_settings.setLayers([layer_terreno])
                rect_mapa = QgsRectangle(mapa_settings.fullExtent())
                rect_mapa.scale(3)
                mapa_settings.setExtent(rect_mapa)
                mapa.setExtent(rect_mapa)
                mapa.attemptResize(QgsLayoutSize(90, 80, QgsUnitTypes.LayoutMillimeters))
                mapa.refresh()
            
            # Añadir texto a las etiquetas
            layout.itemById('id_fecha').setText('{}/{}/{} '.format(now.day, now.month, now.year))
            layout.itemById('name_titular_1').setText(str(feature_terreno["nombre"]) + " " + str(feature_terreno["apellidos"]))
            layout.itemById('name_titular_2').setText(str(feature_terreno["nombre"]) + " " + str(feature_terreno["apellidos"]))
            layout.itemById('predio').setText(str(predio))
            layout.itemById('manzano').setText(str(manzano))
            layout.itemById('distrito').setText(str(distrito))
            layout.itemById('zona').setText(str(feature_terreno["barrio"]))
            layout.itemById('avenida').setText(str(feature_terreno["direccion"]))
            layout.itemById('id_geocodigo').setText('{}'.format(str(feature_terreno['geocod'])))
            layout.itemById('id_codigo_catastral').setText('{}'.format(str(feature_terreno["codigo"])))            
            
           
            layout.itemById('superficie').setText(str(feature_terreno["superficie"]))
            layout.itemById('perimetro').setText(str(feature_terreno["perimetro"]))
            layout.itemById('frente').setText(str(feature_terreno["frente"]))
            layout.itemById('fondo').setText(str(feature_terreno["fondo"]))
            
            layout.itemById('colindante_norte').setText(str(norte))
            layout.itemById('colindante_sur').setText(str(sur))
            layout.itemById('colindante_este').setText(str(este))
            layout.itemById('colindante_oeste').setText(str(oeste))
            
            # Añadir información de co-titulares al layout
            try:
                if layout.itemById('id_cotitulares'):
                    layout.itemById('id_cotitulares').setText(cotitulares_texto)
                else:
                    # Si el elemento no existe en el layout, lo creamos
                    label_cotitulares = QgsLayoutItemLabel(layout)
                    label_cotitulares.setText("CO-TITULARES:")
                    label_cotitulares.setFont(QFont('Arial', 10, QFont.Bold))
                    label_cotitulares.adjustSizeToText()
                    # Ajusta las coordenadas (x,y) según tu layout
                    label_cotitulares.setPos(20, 220)
                    layout.addLayoutItem(label_cotitulares)
                    
                    valor_cotitulares = QgsLayoutItemLabel(layout)
                    valor_cotitulares.setText(cotitulares_texto)
                    valor_cotitulares.setFont(QFont('Arial', 10))
                    valor_cotitulares.adjustSizeToText()
                    valor_cotitulares.setPos(120, 220)  # Ajusta según tu layout
                    layout.addLayoutItem(valor_cotitulares)
            except Exception as ex:
                print(f"Error al mostrar co-titulares en layout: {str(ex)}")
            
            # Calcular la diferencia entre superficie según testimonio y superficie actual
            try:
                # Obtener y validar los valores de superficie
                superficie_actual = 0
                superficie_testimonio = 0
                
                if feature_terreno["superficie"] is not None:
                    superficie_actual = float(feature_terreno["superficie"])
                
                if feature_terreno["suptest"] is not None:
                    superficie_testimonio = float(feature_terreno["suptest"])
                
                # Calcular la diferencia (asumiendo que suptest siempre debe ser mayor)
                if superficie_testimonio > 0:
                    diferencia = superficie_testimonio - superficie_actual
                    porcentaje = (diferencia / superficie_testimonio) * 100
                    
                    if superficie_testimonio >= superficie_actual:
                        texto_diferencia = f"Déficit: {diferencia:.2f} m² ({porcentaje:.2f}%)"
                    else:
                        texto_diferencia = f"{abs(diferencia):.2f} m² ({abs(porcentaje):.2f}%)"
                else:
                    texto_diferencia = "No calculable (sup. testimonio = 0)"
                
                # Verificar si existe el elemento en el layout
                if layout.itemById('id_diferencia_superficie'):
                    layout.itemById('id_diferencia_superficie').setText(texto_diferencia)
                else:
                    print("Elemento 'id_diferencia_superficie' no encontrado en el layout")
            except Exception as e:
                print(f"Error al calcular diferencia de superficies: {str(e)}")    
                sup_test = feature_terreno["suptest"] if feature_terreno["suptest"] else 0
                layout.itemById('id_sup_escritura').setText(f"{sup_test} m²")
            
            # Nuevos datos agregados
            layout.itemById('id_folio_ddrr').setText(str(feature_terreno["folio_ddrr"]))
            layout.itemById('id_n_test').setText(str(feature_terreno["n_test"]))
            layout.itemById('id_fecha_test').setText(str(feature_terreno["fecha_test"]))
            
                        
            from qgis.core import QgsExpression, QgsExpressionContext
            from PyQt5.QtCore import QDate

            # Formatear una fecha específica
            fecha_qdate = feature_terreno['fecha_test']  # O usa 'fecha_testimonio' si existe en feature_terreno
            if isinstance(fecha_qdate, QDate):
                fecha_literal = fecha_qdate.toString("'/'yyyy")
                layout.itemById('id_fecha_test').setText(fecha_literal)
            
        
            
            # Marcar casillas con X para servicios
            feature_data = {field.name(): feature_terreno[field.name()] for field in layer_terreno.fields()}
            if feature_data.get('agua') == 'Si':
                layout.itemById('id_x_agua').setText("X")
            if feature_data.get('luz') == 'Si':
                layout.itemById('id_x_energia').setText("X")
            if feature_data.get('alcantarillado') == 'Si':
                layout.itemById('id_x_alcantarillado').setText("X")
            
            # Mostrar layout
            iface.mapCanvas().setExtent(layer_terreno.extent())
            iface.openLayoutDesigner(layout)
            
            # Exportar PDF
            exporter = QgsLayoutExporter(layout)
            exporter.exportToPdf(self.plugin_dir + '/Informe.pdf', QgsLayoutExporter.PdfExportSettings())
            
            self.driver.showMessage('Informe generado correctamente', 0, 5)
            
        except Exception as e:
            print(f"Error en mostrar_informe: {str(e)}")
            traceback.print_exc()
            self.driver.showMessage(f"Error: {str(e)}", 1, 15)

  

       
       
       
   
   
       
       ############################################################################################################################################
    ############################################################SEXTO BOTON SEGUNDO CERTIFICADO (CATASTRAL)##########################################################
    ############################################################################################################################################ 
    
    lista_terreno_informe2 = ""
    
    def cargar_tablabbdd3(self):
           

        list_widget = self.dlg_informe2.list_bbdd
 

        try:
            r = self.driver.read('select * from catastro.terrenosvista19')

            for i in range(list_widget.count()):
                list_widget.takeItem(0)
            lista = [(str(item["codigo"]) + "   " + str(item["nombre"])  + "   " + str(item["apellidos"])) for item in r]
            list_widget.addItems(lista)
            self.lista_terreno_informe2 = r

        except Exception as ex: 
            print(ex)

        
    
    def listar_layer_informe2_busca_ref(self):
        """Búsqueda por código catastral para informe 2"""
        try:
            list_widget = self.dlg_informe2.list_bbdd
            
            text_busqueda = self.dlg_select_terreno_informe2_busca_ref.text_titular
            valor_busqueda = text_busqueda.toPlainText()
            
            if not valor_busqueda.strip():
                self.driver.showMessage('Ingrese un código para buscar', 1, 15)
                return
                
            # Consulta simple para buscar por código
            sql = f"""
                SELECT codigo, nombre, apellidos, documento 
                FROM catastro.terrenosvista19 
                WHERE codigo ILIKE '%{valor_busqueda}%'
            """
            r = self.driver.read(sql)

            if r:
                list_widget.clear()
                lista = []
                for item in r:
                    if item["nombre"] or item["apellidos"]:
                        lista.append(f"{item['codigo']}   {item['nombre']} {item['apellidos']}")
                    else:
                        lista.append(item["codigo"])
                        
                list_widget.addItems(lista)
                self.lista_terreno_informe2 = r
            else: 
                self.driver.showMessage('No existen registros con este Código Catastral.', 1, 15)
        
        except Exception as e:
            print(f"Error en búsqueda por código: {str(e)}")
            import traceback
            traceback.print_exc()
            self.driver.showMessage(f"Error al buscar: {str(e)}", 2, 5)


    def listar_layer_informe2_busca_nombre(self):
        """Búsqueda por nombre para informe 2"""
        try:
            list_widget = self.dlg_informe2.list_bbdd
            
            text_busqueda = self.dlg_select_terreno_informe2_busca_nombre.text_titular
            valor_busqueda = text_busqueda.toPlainText()
            
            if not valor_busqueda.strip():
                self.driver.showMessage('Ingrese un nombre para buscar', 1, 15)
                return
            
            # Enfoque simple - usar una sola condición ILIKE con el texto completo
            sql = f"""
                SELECT codigo, nombre, apellidos, documento 
                FROM catastro.terrenosvista19 
                WHERE (nombre || ' ' || apellidos) ILIKE '%{valor_busqueda.strip()}%'
            """
            
            r = self.driver.read(sql)
            
            if r:
                list_widget.clear()
                lista = []
                for item in r:
                    if item["nombre"] or item["apellidos"]:
                        lista.append(f"{item['codigo']}   {item['nombre']} {item['apellidos']}")
                    else:
                        lista.append(item["codigo"])
                        
                list_widget.addItems(lista)
                self.lista_terreno_informe2 = r
            else:
                self.driver.showMessage('No existen registros con ese nombre', 1, 15)
        
        except Exception as e:
            print(f"Error en búsqueda por nombre: {str(e)}")
            import traceback
            traceback.print_exc()
            self.driver.showMessage(f"Error al buscar: {str(e)}", 2, 5)
        
         
        
    def mostrar_informe2(self, feature):
        try:
            now = datetime.now()
            finger_print = uuid.uuid4()
            sql_fingerprint = '''INSERT INTO ctrl.cert_catastral
            (uuid)
            VALUES('{}');'''.format(str(finger_print))
            self.driver.create(sql_fingerprint, False)
            sql_serial = '''select concat(lpad((last_value)::text,3,'0'),'/',date_part('Year',current_date)) id  
            from ctrl."cert_catastral_id_seq";'''
            serial = self.driver.read(sql_serial, False, False)
            serial = serial[0]
            QgsProject.instance().removeAllMapLayers()
            
            list_widget = self.dlg_informe2.list_bbdd
            current = list_widget.currentItem()
            
            # Obtengo el texto del QListWidgetItem
            list_widget_name = current.text()
            list_widget_name_ref = ""
            
            for asa in range(len(list_widget_name)):
                if list_widget_name[asa] == " ":
                    ran = asa
                    break
            
            list_widget_name_ref = list_widget_name[0:ran]
            cod_split = list_widget_name_ref.split('.')
            manzano = cod_split[-2]
            predio = cod_split[-1]
            
            ortofoto = QgsRasterLayer(self.ortofoto, 'Ortofoto')
            params = self.driver.params
            
            # 1. Primero cargar la capa de terreno y obtener la característica
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f''' select * from catastro.terrenosvista19 where codigo = '{list_widget_name_ref}' '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            layer_terreno = QgsVectorLayer(uri.uri(False), f'terreno-{list_widget_name_ref}', 'postgres')
            
            layer_terreno.updateExtents()
            
            # Cargar el estilo QML para layer_terreno
            terreno_qml_path = self.plugin_dir + r'\estilos\layer_terreno.qml'
            if os.path.exists(terreno_qml_path):
                success = layer_terreno.loadNamedStyle(terreno_qml_path)
                if success:
                    print(f"Estilo para terreno cargado correctamente")
                else:
                    print(f"Error al cargar estilo para terreno")
            else:
                print(f"Archivo de estilo para terreno no encontrado: {terreno_qml_path}")
            
            layer_terreno.triggerRepaint()
            
            # Obtener feature del terreno para acceder a sus propiedades
            feature_terreno = None
            for feature in layer_terreno.getFeatures():
                feature_terreno = feature
                break
            
            if not feature_terreno:
                raise Exception("No se encontró el terreno en la base de datos")
            
            # Obtener datos completos del terreno de la base de datos
            sql_terreno = f"""
            SELECT * FROM catastro.terrenosvista19 
            WHERE codigo = '{list_widget_name_ref}'
            LIMIT 1
            """
            terreno_data = self.driver.read(sql_terreno)
            if terreno_data and len(terreno_data) > 0:
                terreno = terreno_data[0]  # Tomar el primer resultado
            else:
                terreno = {}  # Terreno vacío como fallback
            
            # 2. Ahora podemos obtener co-titulares usando list_widget_name_ref
            try:
                # Obtenemos el ID del titular principal del terreno
                sql_titular_id = f"""
                SELECT 
                    titular
                FROM 
                    catastro.terrenos19
                WHERE 
                    codigo = '{list_widget_name_ref}'
                LIMIT 1
                """
                
                titular_result = self.driver.read(sql_titular_id)
                
                cotitulares_nombres = []
                
                if titular_result and len(titular_result) > 0 and titular_result[0]['titular'] is not None:
                    titular_id = titular_result[0]['titular']
                    
                    # Ahora buscamos los co-titulares relacionados con este titular
                    sql_cotitulares = f"""
                    SELECT 
                        ct.nombre, 
                        ct.apellidos, 
                        ct.documento
                    FROM 
                        catastro.co_titular ct
                    WHERE 
                        ct.titular_id = {titular_id}
                    ORDER BY 
                        ct.nombre, ct.apellidos
                    """
                    
                    cotitulares_result = self.driver.read(sql_cotitulares)
                    
                    if cotitulares_result:
                        for cotitular in cotitulares_result:
                            nombre = cotitular['nombre'] if cotitular['nombre'] else ""
                            apellidos = cotitular['apellidos'] if cotitular['apellidos'] else ""
                            nombre_completo = f"{nombre} {apellidos}".strip()
                            if nombre_completo:
                                cotitulares_nombres.append(nombre_completo)
                
                cotitulares_texto = ", ".join(cotitulares_nombres) if cotitulares_nombres else "No hay co-titulares"
                print(f"Co-titulares encontrados: {cotitulares_texto}")
            except Exception as ex:
                print(f"Error al obtener co-titulares: {str(ex)}")
                cotitulares_texto = "Error al obtener co-titulares"
            
            # Crear capa de ejes viales
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f'''select ejevias.* from catastro.ejevias
                join catastro.terrenos19 on st_intersects(st_buffer(terrenos19.geom,15),ejevias.geom)
                where terrenos19.codigo = '{list_widget_name_ref}' and st_intersects(st_buffer(terrenos19.geom,15),ejevias.geom) '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            layerEjevias = QgsVectorLayer(uri.uri(False), list_widget_name_ref + '_EjeVias', "postgres")
            layerEjevias.loadNamedStyle(self.plugin_dir + r'\estilos\layer_ejevia.qml')
            layerEjevias.triggerRepaint()
            
            # Configuración para etiquetas de ejes viales
            try:
                # Crear configuración de etiquetado
                label_settings = QgsPalLayerSettings()
                label_settings.enabled = True
                label_settings.fieldName = 'nombre'  # Campo a mostrar en la etiqueta
                
                # Configurar formato del texto
                text_format = QgsTextFormat()
                text_format.setSize(8)  # Tamaño de la fuente
                text_format.setColor(QColor('blue'))  # Color del texto
                text_format.setNamedStyle('Bold')  # Estilo de la fuente
                
                # Fondo blanco para mejor legibilidad
                buffer_settings = QgsTextBufferSettings()
                buffer_settings.setEnabled(True)
                buffer_settings.setSize(0.6)
                buffer_settings.setColor(QColor('white'))
                text_format.setBuffer(buffer_settings)
                
                label_settings.setFormat(text_format)
                
                # Configurar posición
                label_settings.placement = QgsPalLayerSettings.Line
                label_settings.placementFlags = QgsPalLayerSettings.AboveLine
                
                # Aplicar etiquetado
                labeling = QgsVectorLayerSimpleLabeling(label_settings)
                layerEjevias.setLabeling(labeling)
                layerEjevias.setLabelsEnabled(True)
            except Exception as e:
                print(f"Error al configurar etiquetas de ejevias: {str(e)}")
            
            # 3. Crear capa de líneas de medidas
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f'''
            SELECT row_number () over () as id,
                round(cast(st_length(ST_MakeLine(sp, ep)) as numeric), 2) as distancia,
                ST_MakeLine(sp, ep) as geom
            FROM (
                SELECT ST_PointN(geom, generate_series(1, ST_NPoints(geom)-1)) as sp,
                    ST_PointN(geom, generate_series(2, ST_NPoints(geom))) as ep
                FROM (
                    SELECT (ST_Dump(ST_Boundary(geom))).geom
                    FROM catastro.terrenos19
                    WHERE codigo = '{list_widget_name_ref}'
                ) AS linestrings
            ) AS segments
            '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            
            # Usar list_widget_name_ref en lugar de feature_terreno["codigo"]
            layerLineas = QgsVectorLayer(uri.uri(False), list_widget_name_ref + '_Lineas', "postgres")
            layerLineas.loadNamedStyle(self.plugin_dir + r'\estilos\lineas_medidas.qml')
            layerLineas.triggerRepaint()
            
            # 4. Capa colindantes
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f''' select 
                    row_number() OVER () as uid,
                    n.* 
                    from catastro.terrenosvista19 n, catastro.terrenosvista19 p
                    where st_touches(n.geom,p.geom) 
                    and p.codigo = '{list_widget_name_ref}'
                    and n.codigo != '{list_widget_name_ref}' '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'uid')
            layer_colindantes = QgsVectorLayer(uri.uri(False), 'layer_colindantes', 'postgres')
            layer_colindantes.loadNamedStyle(self.plugin_dir + r'\estilos\todos_terrenos.qml')
            layer_colindantes.triggerRepaint()

            # 5. Capa ubicación
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f''' select
                    row_number() OVER () as uid,
                    t.id,
                    t.geom 
                    from catastro.terrenosvista19 t 
                    where t.codigo = '{list_widget_name_ref}' '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'uid')
            layer_ubicacion = QgsVectorLayer(uri.uri(False), f'ubicacion-{list_widget_name_ref}', 'postgres')
            layer_ubicacion.updateExtents()
            layer_ubicacion.loadNamedStyle(self.plugin_dir + r'\estilos\layer_ubicacion.qml')
            layer_ubicacion.triggerRepaint()

            # 6. Consulta para obtener construcciones
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql = f''' select id, numbloque, plantas, anyo, st_area(geom) area, geom 
                    from catastro.construccionesvista19  
                    where codigo = '{list_widget_name_ref}' '''
            uri.setDataSource('', f'({sql})', 'geom', '', 'id')
            layer_construcciones = QgsVectorLayer(uri.uri(False), 'layer_construcciones', 'postgres')

            # Aplicar estilo a la capa de construcciones
            construcciones_qml_path = self.plugin_dir + r'\estilos\layer_construcciones.qml'
            if os.path.exists(construcciones_qml_path):
                success = layer_construcciones.loadNamedStyle(construcciones_qml_path)
                if success:
                    print(f"Estilo para construcciones cargado correctamente")
                else:
                    print(f"Error al cargar estilo para construcciones")
            else:
                print(f"Archivo de estilo no encontrado: {construcciones_qml_path}")

            layer_construcciones.triggerRepaint()
            
            # 7. Procesar áreas de construcciones
            areas_construcciones = {'area_c1': 0, 'area_c2': 0, 'area_c3': 0, 'area_c4': 0, 'area_c5': 0, 'area_c6': 0}
            
            data_construccion = {f['numbloque']: round(f['area'], 2) for f in list(layer_construcciones.getFeatures())}
            i = 1
            for k in areas_construcciones:
                try:
                    areas_construcciones[k] = data_construccion[i]
                    i += 1
                except KeyError:
                    areas_construcciones[k] = 0
            
            c_total = round(sum(areas_construcciones.values()), 2)
            
            # Determinar el tipo de inmueble (TERRENO o CASA) según si hay construcciones
            if c_total > 0:
                tipo_inmueble = "CASA"
            else:
                tipo_inmueble = "TERRENO"

            # 8. Prepara valores para el layout
            titular = '{} {}'.format(terreno['nombre'].upper() if terreno.get('nombre') else '',
                                terreno['apellidos'].upper() if terreno.get('apellidos') else '')
            distrito = terreno.get('zona', '')
            norte, sur, este, oeste = self.getColindantes(list_widget_name_ref)

            # 9. Añadir las capas en el orden correcto
            QgsProject.instance().addMapLayer(ortofoto)
            QgsProject.instance().addMapLayer(layer_colindantes)
            QgsProject.instance().addMapLayer(layer_ubicacion)
            QgsProject.instance().addMapLayer(layerLineas)
            QgsProject.instance().addMapLayer(layerEjevias)
            QgsProject.instance().addMapLayer(layer_terreno)
            QgsProject.instance().addMapLayer(layer_construcciones)
            
            # 10. Crear layout vacío
            project = QgsProject.instance()
            manager = project.layoutManager()
            layout = QgsPrintLayout(project)
            layoutName = "Catastral"
            
            layouts_list = manager.printLayouts()
            for layout in layouts_list:
                if layout.name() == layoutName:
                    manager.removeLayout(layout)
            
            layout = QgsPrintLayout(project)
            layout.initializeDefaults()
            layout.setName(layoutName)
            manager.addLayout(layout)
            
            pc = layout.pageCollection()
            pc.page(0).setPageSize('Letter', QgsLayoutItemPage.Orientation.Portrait)
            
            tmpfile = self.plugin_dir + '/riberaltacatastral.qpt'
            
            with open(tmpfile) as f:
                template_content = f.read()
            
            doc = QDomDocument()
            doc.setContent(template_content)

            items, ok = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)
            
            # 11. Configurar elementos del layout - Acceder con manejo de errores
            def set_layout_text(layout, element_id, text_value, default=""):
                try:
                    item = layout.itemById(element_id)
                    if item:
                        item.setText(str(text_value) if text_value is not None else default)
                except Exception as e:
                    print(f"Error al configurar {element_id}: {str(e)}")
            
            # Configurar todos los elementos del layout con manejo de errores
            set_layout_text(layout, 'id_col_norte', norte)
            set_layout_text(layout, 'id_col_sur', sur)
            set_layout_text(layout, 'id_col_este', este)
            set_layout_text(layout, 'id_col_oeste', oeste)
            set_layout_text(layout, 'id_num_cert', f'N° {str(serial)}')
            set_layout_text(layout, 'id_uuid', f'{str(finger_print)}')
            set_layout_text(layout, 'id_titular', f'{str(titular)}')
            set_layout_text(layout, 'id_propietario', f'{str(titular)}')
            set_layout_text(layout, 'id_distrito', f'{str(terreno.get("zona", ""))}')
            set_layout_text(layout, 'id_distrito_2', f'{str(terreno.get("zona", ""))}')
            set_layout_text(layout, 'id_barrio', f'{str(terreno.get("barrio", ""))}')
            set_layout_text(layout, 'id_direccion', f'{str(terreno.get("direccion", ""))}')
            set_layout_text(layout, 'id_cod_catastral', f'{str(terreno.get("codigo", ""))}')
            set_layout_text(layout, 'id_n_test', f'{str(terreno.get("testimonio", ""))}')
            set_layout_text(layout, 'id_folio_ddrr', f'{str(terreno.get("matricula_ddrr", ""))}')
            set_layout_text(layout, 'id_manzano', f'{str(manzano)}')
            set_layout_text(layout, 'id_lote', f'{str(predio)}')
            set_layout_text(layout, 'id_geocod', str(terreno.get('geocod', "")))
            
            # Establecer el tipo de inmueble según si hay construcciones o no
            set_layout_text(layout, 'id_tipo_inmb', tipo_inmueble)
            
            # Asignar valores de construcciones al layout
            set_layout_text(layout, 'id_c1', f'{areas_construcciones["area_c1"]} m²')
            set_layout_text(layout, 'id_c2', f'{areas_construcciones["area_c2"]} m²')
            set_layout_text(layout, 'id_c3', f'{areas_construcciones["area_c3"]} m²')
            set_layout_text(layout, 'id_c4', f'{areas_construcciones["area_c4"]} m²')
            set_layout_text(layout, 'id_c5', f'{areas_construcciones["area_c5"]} m²')
            set_layout_text(layout, 'id_c6', f'{areas_construcciones["area_c6"]} m²')
            set_layout_text(layout, 'id_ctotal', f'{c_total} m²')
            
            # Añadir información de co-titulares al layout
            try:
                if layout.itemById('id_cotitulares'):
                    layout.itemById('id_cotitulares').setText(cotitulares_texto)
                else:
                    # Si el elemento no existe en el layout, lo creamos
                    label_cotitulares = QgsLayoutItemLabel(layout)
                    label_cotitulares.setText("CO-TITULARES:")
                    label_cotitulares.setFont(QFont('Arial', 10, QFont.Bold))
                    label_cotitulares.adjustSizeToText()
                    # Ajusta las coordenadas (x,y) según tu layout
                    label_cotitulares.setPos(20, 220)
                    layout.addLayoutItem(label_cotitulares)
                    
                    valor_cotitulares = QgsLayoutItemLabel(layout)
                    valor_cotitulares.setText(cotitulares_texto)
                    valor_cotitulares.setFont(QFont('Arial', 10))
                    valor_cotitulares.adjustSizeToText()
                    valor_cotitulares.setPos(120, 220)  # Ajusta según tu layout
                    layout.addLayoutItem(valor_cotitulares)
            except Exception as ex:
                print(f"Error al mostrar co-titulares en layout: {str(ex)}")
                                
            # Convertir QDate a un formato de fecha legible
            try:
                fecha_qdate = terreno.get('fecha_testimonio')
                if isinstance(fecha_qdate, QDate):
                    # Convertir QDate a formato de texto DD/MM/YYYY
                    fecha_texto = fecha_qdate.toString('dd/MM/yyyy')
                else:
                    # Si por alguna razón no es un QDate, usar el valor como está
                    fecha_texto = str(fecha_qdate) if fecha_qdate is not None else ""
                
                # Establecer el texto con el formato correcto
                set_layout_text(layout, 'id_fecha_test', fecha_texto)
            except Exception as e:
                print(f"Error al formatear fecha: {e}")
                # Si hay un error, intentar usar el valor como está
                set_layout_text(layout, 'id_fecha_test', str(terreno.get('fecha_testimonio', '') or ''))
            
            # Formatear una fecha específica
            fecha_qdate = terreno.get('fecha_testimonio')
            if isinstance(fecha_qdate, QDate):
                fecha_literal = fecha_qdate.toString("d 'de' MMMM 'de' yyyy")
                set_layout_text(layout, 'id_fecha_test', fecha_literal)
                
            # Obtener fecha actual formateada
            fecha_actual = QDate.currentDate()
            fecha_actual_texto = fecha_actual.toString("d 'de' MMMM 'de' yyyy")
            
            set_layout_text(layout, 'id_fecha_actual', fecha_actual_texto)
            
            # Manejo seguro de valores numéricos
            sup_test = sup_men = sup_total = 0
            try:
                sup_test = float(terreno.get('suptest', 0) or 0)  # Usar 0 si es None
                sup_test = round(sup_test, 2)
            except (ValueError, TypeError):
                sup_test = 0

            try:
                sup_men = float(terreno.get('superficie', 0) or 0)  # Usar 0 si es None
                sup_men = round(sup_men, 2)
            except (ValueError, TypeError):
                sup_men = 0

            try:
                diferencia = sup_test - sup_men
                sup_total = sup_men + diferencia
                sup_total = round(sup_total, 2)
            except (ValueError, TypeError):
                sup_total = 0

            try:
                antiguedad = int(float(terreno.get('c_antiguedad', 0) or 0))  # Convertir a float primero, luego a int
            except (ValueError, TypeError):
                antiguedad = 0

            # Establecer los valores en el layout con manejo seguro de valores nulos
            set_layout_text(layout, 'id_sup_escritura', f"{sup_test} m²")
            set_layout_text(layout, 'id_sup_men', f"{sup_men} m²")
            set_layout_text(layout, 'id_sup_terre', f"{sup_total} m²")

            # Para el área de construcción, usar manejo seguro
            try:
                area_construccion = float(terreno.get('c_area', 0) or 0)
                set_layout_text(layout, 'id_sup_cons', f"{round(area_construccion, 2)} m²")
            except (ValueError, TypeError):
                set_layout_text(layout, 'id_sup_cons', "0 m²")

            # Resto de los campos del layout
            set_layout_text(layout, 'id_tipo_cons', str(terreno.get('c_tipo', '') or ''))
            set_layout_text(layout, 'id_const_ant', f"{int(now.year) - antiguedad} años")
            set_layout_text(layout, 'id_tipo_via', str(terreno.get('tipovia', '') or ''))
            set_layout_text(layout, 'id_serv_luz', "Si" if terreno.get('luz') else "No")
            set_layout_text(layout, 'id_serv_agua', "Si" if terreno.get('agua') else "No")
            set_layout_text(layout, 'id_serv_tel', "Si" if terreno.get('telefono') else "No")
            set_layout_text(layout, 'id_serv_alcant', "Si" if terreno.get('alcantarillado') else "No")
            set_layout_text(layout, 'id_material_via', str(terreno.get('materialvia', '') or ''))
            
            # 12. Configurar los mapas
            croquis = layout.itemById('id_croquis')
            if croquis:
                croquis_settings = QgsMapSettings()
                croquis.setLayers([layer_ubicacion, layerEjevias, layer_construcciones, ortofoto])
                croquis_settings.setLayers([layer_ubicacion, layer_construcciones])
                rect_croquis = QgsRectangle(croquis_settings.fullExtent())
                rect_croquis.scale(3)
                croquis_settings.setExtent(rect_croquis)
                croquis.setExtent(rect_croquis)
                croquis.attemptResize(QgsLayoutSize(80, 80, QgsUnitTypes.LayoutMillimeters))

            # Para el plano
            plano = layout.itemById('id_plano')
            if plano:
                plano_settings = QgsMapSettings()
                plano.setLayers([layer_terreno, layerLineas, layer_colindantes, layer_construcciones])
                plano_settings.setLayers([layer_terreno])
                rect_plano = QgsRectangle(plano_settings.fullExtent())
                rect_plano.scale(3)
                plano_settings.setExtent(rect_plano)
                plano.setExtent(rect_plano)
                plano.attemptResize(QgsLayoutSize(80, 80, QgsUnitTypes.LayoutMillimeters))
            
            iface.mapCanvas().setExtent(layer_terreno.extent())
            iface.openLayoutDesigner(layout)
                                
            exporter = QgsLayoutExporter(layout)
            exporter.exportToPdf(self.plugin_dir + '/CertificadoCatastral.pdf', QgsLayoutExporter.PdfExportSettings())

        except Exception as ex:
            print(f"Error detallado: {str(ex)}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self.dlg_informe2, "Error", f"Error al procesar los datos: {str(ex)}")
            return 
    
    
    
    
    ############################################################################################################################################
    ############################################################SEPTIMO BOTON TERCER CERTIFICADO (AVALUO)##########################################################
    ############################################################################################################################################ 
    
    def listar_layer_informe3_busca_ref(self):
        """Búsqueda por código catastral para informe 3"""
        try:
            list_widget = self.dlg_informe3.list_bbdd
            text_busqueda = self.dlg_select_terreno_informe3_busca_ref.text_titular
            valor_busqueda = text_busqueda.toPlainText()

            sql = f"""
                SELECT codigo, nombre, apellidos 
                FROM catastro.terrenosvista19 
                WHERE codigo ILIKE '%{valor_busqueda}%'
                ORDER BY codigo
            """
            r = self.driver.read(sql)

            if r:
                list_widget.clear()
                lista = [f"{item['codigo']}   {item['nombre']} {item['apellidos']}" for item in r]
                list_widget.addItems(lista)
                self.lista_terreno_informe3 = r
            else:
                self.driver.showMessage('No existen registros con ese código catastral', 1, 5)

        except Exception as e:
            print(f"Error en búsqueda por código: {str(e)}")
            self.driver.showMessage("Error al buscar", 2, 5)

    def listar_layer_informe3_busca_ref(self):
        """Búsqueda por código catastral para informe 3"""
        try:
            list_widget = self.dlg_informe3.list_bbdd
            text_busqueda = self.dlg_select_terreno_informe3_busca_ref.text_titular
            valor_busqueda = text_busqueda.toPlainText()

            sql = f"""
                SELECT codigo, nombre, apellidos 
                FROM catastro.terrenosvista19 
                WHERE codigo ILIKE '%{valor_busqueda}%'
                ORDER BY codigo
            """
            r = self.driver.read(sql)

            if r:
                list_widget.clear()
                lista = [f"{item['codigo']}   {item['nombre']} {item['apellidos']}" for item in r]
                list_widget.addItems(lista)
                self.lista_terreno_informe3 = r
            else:
                self.driver.showMessage('No existen registros con ese código catastral', 1, 5)

        except Exception as e:
            print(f"Error en búsqueda por código: {str(e)}")
            self.driver.showMessage("Error al buscar", 2, 5)
    
    def listar_layer_informe3_busca_nombre(self):
        """Búsqueda por nombre para informe 3"""
        try:
            list_widget = self.dlg_informe3.list_bbdd
            text_busqueda = self.dlg_select_terreno_informe3_busca_nombre.text_titular
            valor_busqueda = text_busqueda.toPlainText()

            # Construir búsqueda con ILIKE para cada palabra
            palabras = valor_busqueda.split()
            condicion = ""
            for palabra in palabras:
                condicion += f"(nombre || ' ' || apellidos) ILIKE '%{palabra}%' AND "
            
            sql = f"""
                SELECT codigo, nombre, apellidos 
                FROM catastro.terrenosvista19 
                WHERE {condicion[:-5]}
                ORDER BY codigo
            """
            r = self.driver.read(sql)

            if r:
                list_widget.clear()
                lista = [f"{item['codigo']}   {item['nombre']} {item['apellidos']}" for item in r]
                list_widget.addItems(lista)
                self.lista_terreno_informe3 = r
            else:
                self.driver.showMessage('No existen registros con ese nombre', 1, 5)

        except Exception as e:
            print(f"Error en búsqueda por nombre: {str(e)}")
            self.driver.showMessage("Error al buscar", 2, 5)
    
    
    def mostrar_informe3(self):
        """Generar informe técnico de transferencia"""
        try:
            # Limpiar todas las capas existentes en QGIS
            QgsProject.instance().removeAllMapLayers()
            
            # Obtener código del terreno seleccionado
            list_widget = self.dlg_informe3.list_bbdd
            current = list_widget.currentItem()
            if not current:
                self.driver.showMessage('Seleccione un terreno', 1, 15)
                return
                
            codigo = current.text().split()[0]
            cod_split = codigo.split('.')
            manzano = cod_split[-2] if len(cod_split) >= 2 else ""
            predio = cod_split[-1] if len(cod_split) >= 1 else ""

            # Configurar conexión
            params = self.driver.params
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], 
                            params['user'], params['password'])

            # Consulta SQL para terreno
            sql = f"""
                SELECT 
                    row_number() OVER () as uid,  -- Agregamos un ID único
                    t.id,
                    t.codigo,
                    t.geocod,
                    t.zona,
                    t.barrio,
                    t.direccion,
                    t.n_test,
                    t.fecha_test, 
                    t.folio_ddrr, 
                    t.manzano,
                    t.predio, 
                    t.suptest,
                    t.superficie,
                    t.nombre,
                    t.apellidos,
                    t.n_test testimonio,
                    t.fecha_test fecha_testimonio,
                    t.folio_ddrr matricula_ddrr,
                    c.area c_area,
                    tc.tipo c_tipo,
                    c.antiguedad c_antiguedad,
                    t.tipovia,
                    (case when t.energia then 'Si' else 'No' end) luz,
                    (case when t.agua then 'Si' else 'No' end) agua,
                    (case when t.telefono then 'Si' else 'No' end) telefono,
                    (case when t.alcantarillado then 'Si' else 'No' end) alcantarillado,
                    (case when c.area > 0 then 'Vivienda' else 'Terreno' end) tipo_inmueble,
                    (case 
                        when t.material_via = 1 then 'Asfalto'
                        when t.material_via = 2 then 'Adoquín'
                        when t.material_via = 3 then 'Cemento'
                        when t.material_via = 4 then 'Loseta'
                        when t.material_via = 5 then 'Piedra'
                        when t.material_via = 6 then 'Ripio'
                        when t.material_via = 7 then 'Tierra'
                        else 'No especificado'
                    end) as material_via_desc,
                    t.geom 
                FROM catastro.terrenosvista19 t 
                LEFT JOIN (
                    SELECT codigo, sum(st_area(geom)) area, max(tipo) tipo, min(anyo) antiguedad 
                    FROM catastro.construccionesvista19 
                    GROUP BY codigo
                ) as c ON c.codigo = t.codigo
                LEFT JOIN catastro.tipo_construccion tc ON tc.id = c.tipo
                WHERE t.codigo = '{codigo}'
            """
            
            # Código para obtener co-titulares
            try:
                # Obtenemos el ID del titular principal del terreno
                sql_titular_id = f"""
                SELECT 
                    titular
                FROM 
                    catastro.terrenos19
                WHERE 
                    codigo = '{feature_terreno["codigo"]}'
                LIMIT 1
                """
                
                titular_result = self.driver.read(sql_titular_id)
                
                cotitulares_nombres = []
                
                if titular_result and len(titular_result) > 0 and titular_result[0]['titular'] is not None:
                    titular_id = titular_result[0]['titular']
                    
                    # Ahora buscamos los co-titulares relacionados con este titular
                    sql_cotitulares = f"""
                    SELECT 
                        ct.nombre, 
                        ct.apellidos, 
                        ct.documento
                    FROM 
                        catastro.co_titular ct
                    WHERE 
                        ct.titular_id = {titular_id}
                    ORDER BY 
                        ct.nombre, ct.apellidos
                    """
                    
                    cotitulares_result = self.driver.read(sql_cotitulares)
                    
                    if cotitulares_result:
                        for cotitular in cotitulares_result:
                            nombre = cotitular['nombre'] if cotitular['nombre'] else ""
                            apellidos = cotitular['apellidos'] if cotitular['apellidos'] else ""
                            nombre_completo = f"{nombre} {apellidos}".strip()
                            if nombre_completo:
                                cotitulares_nombres.append(nombre_completo)
                
                cotitulares_texto = ", ".join(cotitulares_nombres) if cotitulares_nombres else "No hay co-titulares"
                print(f"Co-titulares encontrados: {cotitulares_texto}")
            except Exception as ex:
                print(f"Error al obtener co-titulares: {str(ex)}")
                cotitulares_texto = "Error al obtener co-titulares"
            
            # Crear capa de terreno con toda la información
            uri.setDataSource('', f'({sql})', 'geom', '', 'uid')
            layer_terreno = QgsVectorLayer(uri.uri(False), f'terreno-{codigo}', 'postgres')

            if not layer_terreno.isValid():
                self.driver.showMessage('Error al crear capa de terreno', 1, 15)
                return
                
            # Cargar estilo para el terreno
            try:
                layer_terreno.loadNamedStyle(self.plugin_dir + r'\estilos\layer_terreno.qml')
            except Exception as e:
                print(f"Error al cargar estilo de terreno: {str(e)}")

            # Obtener datos de construcciones
            sql_const = f"""
                SELECT id, numbloque, plantas, anyo, st_area(geom) as area, geom
                FROM catastro.construccionesvista19 
                WHERE codigo = '{codigo}'
            """
            uri.setDataSource('', f'({sql_const})', 'geom', '', 'id')
            layer_construcciones = QgsVectorLayer(uri.uri(False), 'layer_construcciones', 'postgres')
            
            # Cargar estilo para las construcciones
            try:
                layer_construcciones.loadNamedStyle(self.plugin_dir + r'\estilos\layer_construcciones.qml')
            except Exception as e:
                print(f"Error al cargar estilo de construcciones: {str(e)}")
            
            # Capa de colindantes (predios vecinos)
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql_colindantes = f"""
                SELECT 
                    row_number() OVER () as uid,
                    n.* 
                FROM catastro.terrenosvista19 n, catastro.terrenosvista19 p
                WHERE st_touches(n.geom, p.geom) 
                    AND p.codigo = '{codigo}'
                    AND n.codigo != '{codigo}'
            """
            uri.setDataSource('', f'({sql_colindantes})', 'geom', '', 'uid')
            layer_colindantes = QgsVectorLayer(uri.uri(False), 'layer_colindantes', 'postgres')
            
            # Cargar estilo para los colindantes
            try:
                layer_colindantes.loadNamedStyle(self.plugin_dir + r'\estilos\todos_terrenos.qml')
            except Exception as e:
                print(f"Error al cargar estilo de colindantes: {str(e)}")
            
            layer_colindantes.triggerRepaint()
            
            # Capa de ubicación para el mapa
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql_ubicacion = f"""
                SELECT 
                    row_number() OVER () as uid,
                    t.id,
                    t.geom 
                FROM catastro.terrenosvista19 t 
                WHERE t.codigo = '{codigo}'
            """
            uri.setDataSource('', f'({sql_ubicacion})', 'geom', '', 'uid')
            layer_ubicacion = QgsVectorLayer(uri.uri(False), f'ubicacion-{codigo}', 'postgres')
            layer_ubicacion.updateExtents()
            
            try:
                layer_ubicacion.loadNamedStyle(self.plugin_dir + r'\estilos\layer_ubicacion.qml')
            except Exception as e:
                print(f"Error al cargar estilo de ubicación: {str(e)}")
            
            layer_ubicacion.triggerRepaint()
            
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql_ejevias = f"""
                SELECT id, nombre, geom
                FROM catastro.ejevias
                WHERE ST_DWithin(geom, (SELECT geom FROM catastro.terrenosvista19 WHERE codigo = '{codigo}'), 100)
            """
            uri = QgsDataSourceUri()
            uri.setConnection(params['host'], params['port'], params['dbname'], params['user'], params['password'])
            sql_ejevias = f"""
                SELECT id, nombre, geom
                FROM catastro.ejevias
                WHERE ST_DWithin(geom, (SELECT geom FROM catastro.terrenosvista19 WHERE codigo = '{codigo}'), 100)
            """
            uri.setDataSource('', f'({sql_ejevias})', 'geom', '', 'id')
            layer_ejevias = QgsVectorLayer(uri.uri(False), 'layer_ejevias', 'postgres')

            # Cargar estilo para ejevias desde el archivo .qml
            try:
                layer_ejevias.loadNamedStyle(self.plugin_dir + r'\estilos\layer_ejevia.qml')
            except Exception as e:
                print(f"Error al cargar estilo de ejevias: {str(e)}")

            # Configurar el etiquetado para las ejevias
            try:
                # Crear configuración de etiquetado
                label_settings = QgsPalLayerSettings()
                label_settings.enabled = True
                label_settings.fieldName = 'nombre'  # Campo a mostrar en la etiqueta
                
                # Configurar formato del texto
                text_format = QgsTextFormat()
                text_format.setSize(8)  # Tamaño de la fuente
                text_format.setColor(QColor('blue'))  # Color del texto
                text_format.setNamedStyle('Bold')  # Estilo de la fuente
                
                # Fondo blanco para mejor legibilidad
                buffer_settings = QgsTextBufferSettings()
                buffer_settings.setEnabled(True)
                buffer_settings.setSize(0.5)
                buffer_settings.setColor(QColor('white'))
                text_format.setBuffer(buffer_settings)
                
                label_settings.setFormat(text_format)
                
                # Configurar posición
                label_settings.placement = QgsPalLayerSettings.Line
                label_settings.placementFlags = QgsPalLayerSettings.AboveLine
                
                # Aplicar etiquetado
                labeling = QgsVectorLayerSimpleLabeling(label_settings)
                layer_ejevias.setLabeling(labeling)
                layer_ejevias.setLabelsEnabled(True)
            except Exception as e:
                print(f"Error al configurar etiquetas de ejevias: {str(e)}")

            layer_ejevias.triggerRepaint()

                  
            
            # Añadir ortofoto si está disponible
            try:
                ortofoto = QgsRasterLayer(self.ortofoto, 'Ortofoto')
                if ortofoto.isValid():
                    QgsProject.instance().addMapLayer(ortofoto)
            except Exception as e:
                print(f"Error al cargar ortofoto: {str(e)}")
                ortofoto = None

            # Verificar si se obtuvieron datos del terreno
            if layer_terreno.featureCount() == 0:
                self.driver.showMessage('No se encontró el terreno especificado', 1, 15)
                return
                
            # Obtener la primera feature del terreno
            features = list(layer_terreno.getFeatures())
            terreno = features[0]
            
            # Obtener datos de construcción antigua/nueva
            construccion_antigua = 0
            construccion_nueva = 0
            
            for f in layer_construcciones.getFeatures():
                try:
                    # Consideramos construcción antigua si es anterior a 2000
                    if int(f["anyo"]) < 2000:
                        construccion_antigua += f["area"]
                    else:
                        construccion_nueva += f["area"]
                except (ValueError, TypeError):
                    # Si hay error al convertir el año, asumimos que es construcción antigua
                    construccion_antigua += f["area"]

            # Añadir capas al proyecto en el orden correcto
            if 'ortofoto' in locals() and ortofoto and ortofoto.isValid():
                QgsProject.instance().addMapLayer(ortofoto)  # Primero ortofoto (fondo)
            
            QgsProject.instance().addMapLayer(layer_colindantes)  # Luego colindantes
            QgsProject.instance().addMapLayer(layer_ubicacion)  # Luego ubicación
            QgsProject.instance().addMapLayer(layer_ejevias)
            QgsProject.instance().addMapLayer(layer_terreno)  # Luego terreno
            QgsProject.instance().addMapLayer(layer_construcciones)  # Finalmente construcciones

            # Consulta para obtener datos de vendedores y compradores
            sql_transferencia = f"""
                SELECT 
                    codigo_terreno,
                    nombre_titular_anterior, 
                    apellidos_titular_anterior,
                    documento_titular_anterior,
                    nombre_nuevo_titular,
                    apellidos_nuevo_titular,
                    documento_nuevo_titular,
                    nombre_co_titular,
                    apellidos_co_titular,
                    documento_co_titular,
                    year_transfer, 
                    month_transfer, 
                    day_transfer
                FROM historial_transferencias
                WHERE codigo_terreno = '{codigo}'
                ORDER BY year_transfer DESC, month_transfer DESC, day_transfer DESC
                LIMIT 1
            """
            
            # Ejecutar consulta de transferencia
            datos_transferencia = self.driver.read(sql_transferencia)
            
            # Consulta para obtener IDs de construcción para el terreno
            sql_ids = f"""
                SELECT id
                FROM catastro.construccionesvista19
                WHERE codigo = '{codigo}'
            """
            ids_construccion = self.driver.read(sql_ids)

            # Si hay construcciones, consultamos sus plantas
            datos_materiales = []
            if ids_construccion:
                # Construir lista de IDs para la cláusula IN
                ids_list = ", ".join([str(row['id']) for row in ids_construccion])
                
                # Consulta para obtener materiales de construcción
                sql_materiales = f"""
                    SELECT 
                        id_planta,
                        cimiento,
                        estructura,
                        muros,
                        muros_ext,
                        muros_int,
                        cubierta,
                        pisos,
                        carpinteria,
                        anyo,
                        superficie
                    FROM construcciones_plantas19
                    WHERE id_construccion IN ({ids_list})
                    ORDER BY id_planta
                """
                datos_materiales = self.driver.read(sql_materiales)

            # Crear layout
            project = QgsProject.instance()
            manager = project.layoutManager()
            layoutName = "Informe_Transferencia"

            # Eliminar layout existente
            layouts_list = manager.printLayouts()
            for l in layouts_list:
                if l.name() == layoutName:
                    manager.removeLayout(l)

            # Configurar nuevo layout
            layout = QgsPrintLayout(project)
            layout.initializeDefaults()
            layout.setName(layoutName)
            manager.addLayout(layout)
            
            # Configurar orientación de página
            pc = layout.pageCollection()
            pc.page(0).setPageSize('legal', QgsLayoutItemPage.Orientation.Portrait)

            # Cargar plantilla
            tmpfile = self.plugin_dir + '/transferencia.qpt'
            with open(tmpfile) as f:
                template_content = f.read()

            doc = QDomDocument()
            doc.setContent(template_content)
            
            # Cargar la plantilla en el layout
            items, ok = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)
            
            # Verificar si se cargó correctamente la plantilla
            if not ok:
                self.driver.showMessage('Error al cargar la plantilla', 1, 15)
                return
            
            # Obtener la fecha actual
            now = datetime.now()
            hr_number = ""  # Este podría ser un número generado o asignado
            
            # Información general
            layout.itemById('id_numero_informe').setText(f"N° {now.strftime('%Y')}/{now.month:02d}")
            layout.itemById('id_hr').setText('{}'.format(hr_number))
            layout.itemById('id_anio').setText('{}'.format(str(now.year)))
            
            # Datos de vendedores y compradores desde historial_transferencias
            if datos_transferencia:
                # Datos del vendedor (titular anterior)
                vendedor = datos_transferencia[0]
                nombre_vendedor = f"{vendedor['nombre_titular_anterior']} {vendedor['apellidos_titular_anterior']}".upper()
                layout.itemById('id_nombres_vendedores').setText('{}'.format(nombre_vendedor))
                layout.itemById('id_pmc_vendedores').setText('{}'.format(str(vendedor['documento_titular_anterior'])))
                
                # Datos del comprador (nuevo titular)
                nombre_comprador = f"{vendedor['nombre_nuevo_titular']} {vendedor['apellidos_nuevo_titular']}".upper()
                layout.itemById('id_nombres_compradores').setText('{}'.format(nombre_comprador))
                layout.itemById('id_pmc_compradores').setText('{}'.format(str(vendedor['documento_nuevo_titular'])))
                
                # Si hay co-titular, agregar al campo de compradores
                if vendedor['nombre_co_titular']:
                    nombre_co_titular = f"{vendedor['nombre_co_titular']} {vendedor['apellidos_co_titular']}".upper()
                    layout.itemById('id_nombres_compradores').setText('{}\n{}'.format(nombre_comprador, nombre_co_titular))
            else:
                # Si no hay datos de transferencia, usar datos del terreno como propietario actual
                nombre_propietario = f"{terreno['nombre']} {terreno['apellidos']}".upper()
                layout.itemById('id_nombres_vendedores').setText('{}'.format(nombre_propietario))
            
            # Ubicación y códigos
            layout.itemById('id_ubicacion').setText('{}'.format(str(terreno['direccion'])))
            layout.itemById('id_geocodigo').setText('{}'.format(str(terreno['geocod'])))
            layout.itemById('id_codigo_catastral').setText('{}'.format(str(terreno['codigo'])))
            
            # Datos del terreno
            layout.itemById('id_superficie_testimonio').setText('{} m2'.format(str(terreno['suptest'])))
            layout.itemById('id_registro_ddrr').setText('{}'.format(str(terreno['matricula_ddrr'])))
            
            # Datos de construcción
            layout.itemById('id_const_antigua').setText('{} m2'.format(str(round(construccion_antigua, 2))))
            layout.itemById('id_const_nueva').setText('{} m2'.format(str(round(construccion_nueva, 2))))
            layout.itemById('id_total_const').setText('{} m2'.format(str(round(construccion_antigua + construccion_nueva, 2))))
            
            # Marcar casillas con X para tipo de vía
            if terreno['material_via_desc'] == 'Tierra':
                layout.itemById('id_x_tierra').setText("X")
            elif terreno['material_via_desc'] == 'Empedrado':
                layout.itemById('id_x_empedrado').setText("X")
            elif terreno['material_via_desc'] == 'Asfalto':
                layout.itemById('id_x_asfalto').setText("X")
            elif terreno['material_via_desc'] == 'Loseta':
                layout.itemById('id_x_enlosetado').setText("X")
            
            # Añadir información de co-titulares al layout
            try:
                if layout.itemById('id_cotitulares'):
                    layout.itemById('id_cotitulares').setText(cotitulares_texto)
                else:
                    # Si el elemento no existe en el layout, lo creamos
                    label_cotitulares = QgsLayoutItemLabel(layout)
                    label_cotitulares.setText("CO-TITULARES:")
                    label_cotitulares.setFont(QFont('Arial', 10, QFont.Bold))
                    label_cotitulares.adjustSizeToText()
                    # Ajusta las coordenadas (x,y) según tu layout
                    label_cotitulares.setPos(20, 220)
                    layout.addLayoutItem(label_cotitulares)
                    
                    valor_cotitulares = QgsLayoutItemLabel(layout)
                    valor_cotitulares.setText(cotitulares_texto)
                    valor_cotitulares.setFont(QFont('Arial', 10))
                    valor_cotitulares.adjustSizeToText()
                    valor_cotitulares.setPos(120, 220)  # Ajusta según tu layout
                    layout.addLayoutItem(valor_cotitulares)
            except Exception as ex:
                print(f"Error al mostrar co-titulares en layout: {str(ex)}")
            
            # Marcar casillas con X para servicios
            if terreno['agua'] == 'Si':
                layout.itemById('id_x_agua').setText("X")
            if terreno['luz'] == 'Si':
                layout.itemById('id_x_energia').setText("X")
            if terreno['alcantarillado'] == 'Si':
                layout.itemById('id_x_alcantarillado').setText("X")
            
            tiene_construcciones = layer_construcciones.featureCount() > 0    
            # Marcar casillas con X para tipo de inmueble
            if tiene_construcciones:
                layout.itemById('id_x_casa').setText("X")
                layout.itemById('id_x_terreno').setText("")  # Asegurar que terreno no está marcado
            else:
                layout.itemById('id_x_casa').setText("")  # Asegurar que casa no está marcada
                layout.itemById('id_x_terreno').setText("X")
            
            # Procesar datos de materiales por bloque
            if datos_materiales:
                # Mapeo de materiales a sus IDs en el layout
                # Los nombres de estos IDs deben ajustarse según tu plantilla
                materiales_mapping = {
                    # Cimientos
                    1: 'id_x_cimiento_hormigonarmado_b',  # Hormigón armado
                    2: 'id_x_cimiento_hormigonciclopeo_b', # Hormigón ciclópeo
                    3: 'id_x_cimiento_ladrillocemento_b',  # Ladrillo cemento
                    4: 'id_x_cimiento_piedrabarro_b',     # Piedra y barro
                    
                    # Estructuras
                    5: 'id_x_estructura_hormigon_b',      # Hormigón
                    6: 'id_x_estructura_ladrillo_b',      # Ladrillo
                    7: 'id_x_estructura_piedra_b',        # Piedra
                    
                    # Cubierta
                    8: 'id_x_cubierta_losa_b',           # Losa H.A.
                    9: 'id_x_cubierta_tejas_b',          # Tejas
                    10: 'id_x_cubierta_calaminas_b',      # Calaminas
                    11: 'id_x_cubierta_paja_b',           # Paja
                    
                    # Muros
                    12: 'id_x_muros_hormigon_b',         # Hormigon
                    13: 'id_x_muros_ladrillo_b',         # Ladrillo
                    14: 'id_x_muros_madera_b',           # Madera
                    15: 'id_x_muros_adobe_b',            # Adobe
                    
                    # Revestimiento exterior
                    16: 'id_x_revest_ceramica_b',        # Cerámica
                    17: 'id_x_revest_piedra_b',          # Piedra
                    18: 'id_x_revest_ladrillovisto_b',   # Ladrillo Visto
                    19: 'id_x_revest_yesopintado_b',     # Yeso Pintado
                    20: 'id_x_revest_rebcalcemen_b',     # Reb.Cal.Cemen
                    
                    # Carpintería
                    21: 'id_x_carpinteria_aluminio_b',   # Aluminio
                    22: 'id_x_carpinteria_madera_b',     # Madera
                    23: 'id_x_carpinteria_metal_b',      # Metal
                    24: 'id_x_carpinteria_sinpuerta_b',  # Sin Puerta Vent
                    
                    # Pisos
                    25: 'id_x_pisos_ceramica_b',         # Cerámica
                    26: 'id_x_pisos_parquet_b',          # Parquet
                    27: 'id_x_pisos_machimbre_b',        # Machimbre
                    28: 'id_x_pisos_cemento_b',          # Cemento
                    29: 'id_x_pisos_tierra_b',           # Tierra
                    
                    # Revestimiento interior
                    30: 'id_x_revint_ceramica_b',        # Cerámica
                    31: 'id_x_revint_piedra_b',          # Piedra
                    32: 'id_x_revint_revcalcement_b',    # Rev.Cal.Cement
                    33: 'id_x_revint_ladrillo_b'         # Ladrillo
                }
                
                # Procesar cada bloque de construcción
                for i, material in enumerate(datos_materiales, 1):
                    # Limitar a 4 bloques como máximo (según el layout)
                    if i > 4:
                        break
                    
                    # Marcar cimientos
                    if material['cimiento'] and material['cimiento'] in materiales_mapping:
                        id_elemento = materiales_mapping[material['cimiento']] + str(i)
                        layout.itemById(id_elemento).setText("X")
                    
                    # Marcar estructura
                    if material['estructura'] and material['estructura'] in materiales_mapping:
                        id_elemento = materiales_mapping[material['estructura']] + str(i)
                        layout.itemById(id_elemento).setText("X")
                    
                    # Marcar muros
                    if material['muros'] and material['muros'] in materiales_mapping:
                        id_elemento = materiales_mapping[material['muros']] + str(i)
                        layout.itemById(id_elemento).setText("X")
                    
                    # Marcar revestimiento exterior
                    if material['muros_ext'] and material['muros_ext'] in materiales_mapping:
                        id_elemento = materiales_mapping[material['muros_ext']] + str(i)
                        layout.itemById(id_elemento).setText("X")
                    
                    # Marcar revestimiento interior
                    if material['muros_int'] and material['muros_int'] in materiales_mapping:
                        id_elemento = materiales_mapping[material['muros_int']] + str(i)
                        layout.itemById(id_elemento).setText("X")
                    
                    # Marcar cubierta
                    if material['cubierta'] and material['cubierta'] in materiales_mapping:
                        id_elemento = materiales_mapping[material['cubierta']] + str(i)
                        layout.itemById(id_elemento).setText("X")
                    
                    # Marcar pisos
                    if material['pisos'] and material['pisos'] in materiales_mapping:
                        id_elemento = materiales_mapping[material['pisos']] + str(i)
                        layout.itemById(id_elemento).setText("X")
                    
                    # Marcar carpintería
                    if material['carpinteria'] and material['carpinteria'] in materiales_mapping:
                        id_elemento = materiales_mapping[material['carpinteria']] + str(i)
                        layout.itemById(id_elemento).setText("X")
            
            # Datos adicionales
            #layout.itemById('id_n_test').setText('{}'.format(str(terreno['testimonio'])))
            #layout.itemById('id_folio_ddrr').setText('{}'.format(str(terreno['matricula_ddrr'])))
            #layout.itemById('id_manzano').setText('{}'.format(str(manzano)))
            layout.itemById('id_lote').setText('{}'.format(str(predio)))
            #layout.itemById('id_geocod').setText(str(terreno['geocod']))
            
            # Configurar mapa de ubicación (con ortofoto)
           
            mapa_ubicacion = layout.itemById('id_mapa_ubicacion')
            if mapa_ubicacion and isinstance(mapa_ubicacion, QgsLayoutItemMap):
                # Configurar capas del mapa en el orden correcto
                capas_ubicacion = []
                if 'ortofoto' in locals() and ortofoto and ortofoto.isValid():
                    capas_ubicacion.append(ortofoto)  # Ortofoto primero (fondo)
                capas_ubicacion.append(layer_ubicacion)  # Luego la capa de ubicación
                capas_ubicacion.append(layer_ejevias)
                capas_ubicacion.append(layer_terreno)  # Luego el terreno
                capas_ubicacion.append(layer_construcciones)  # Finalmente las construcciones
                
                # Establecer las capas en el mapa
                mapa_ubicacion.setLayers([layer_construcciones, layer_terreno, layer_ejevias, layer_ubicacion, ortofoto])
                
                # Configurar la extensión basada en la capa de ubicación
                ms2 = QgsMapSettings()
                ms2.setLayers([layer_ubicacion])  # Usar layer_ubicacion para determinar la extensión
                
                # Obtener la extensión completa y escalarla
                rect2 = QgsRectangle(ms2.fullExtent())
                rect2.scale(3)  # Ajustar la escala para mostrar más contexto, como en tu ejemplo
                
                # Establecer la extensión y forzar actualización
                mapa_ubicacion.setExtent(rect2)
                mapa_ubicacion.refresh()# Configurar mapa de ubicación (con ortofoto)
                mapa_ubicacion = layout.itemById('id_mapa_ubicacion')
                if mapa_ubicacion and isinstance(mapa_ubicacion, QgsLayoutItemMap):
                    # IMPORTANTE: Invertir el orden de las capas para que la ortofoto esté en el fondo
                    # y las construcciones/terrenos encima
                    ms2 = QgsMapSettings()
                    ms2.setLayers([layer_ubicacion])  # Usar layer_ubicacion para determinar la extensión
                    
                    # Configurar las capas en el orden correcto para la visualización
                    # La ortofoto debe ser la última en la lista para que aparezca en el fondo
                    mapa_ubicacion.setLayers([layer_construcciones, layer_terreno, layer_ejevias, layer_ubicacion, ortofoto])
                    
                    # Obtener la extensión completa y escalarla
                    rect2 = QgsRectangle(ms2.fullExtent())
                    rect2.scale(5)  # Ajustar la escala para mostrar más contexto
                    
                    # Establecer la extensión y forzar actualización
                    mapa_ubicacion.setExtent(rect2)
                    
                    # Ajustar el tamaño del mapa
                    mapa_ubicacion.attemptResize(QgsLayoutSize(95, 80, QgsUnitTypes.LayoutMillimeters))
                    mapa_ubicacion.refresh()
            
            # Configurar mapa del plano (sin ortofoto)
            mapa_plano = layout.itemById('id_plano')
            if mapa_plano and isinstance(mapa_plano, QgsLayoutItemMap):
                plano_settings = QgsMapSettings()
                
                # Capas para el mapa del plano
                mapa_plano.setLayers([layer_terreno, layer_colindantes, layer_construcciones])
                plano_settings.setLayers([layer_terreno])
                rect_plano = QgsRectangle(plano_settings.fullExtent())
                rect_plano.scale(3)
                plano_settings.setExtent(rect_plano)
                mapa_plano.setExtent(rect_plano)
                mapa_plano.attemptResize(QgsLayoutSize(95, 80, QgsUnitTypes.LayoutMillimeters))
                mapa_plano.refresh()
            
            # Enfoca la vista principal de QGIS en el terreno
            iface.mapCanvas().setExtent(layer_terreno.extent())
            
            # Mostrar layout
            iface.openLayoutDesigner(layout)

            # Exportar PDF
            pdf_filename = f"Informe_Transferencia_{codigo}.pdf"
            exporter = QgsLayoutExporter(layout)
            exporter.exportToPdf(self.plugin_dir + f'/{pdf_filename}', QgsLayoutExporter.PdfExportSettings())
            
            self.driver.showMessage(f"Informe generado como {pdf_filename}", 0, 5)

        except Exception as e:
            print(f"Error en mostrar_informe3: {str(e)}")
            traceback.print_exc()
            self.driver.showMessage(f"Error: {str(e)}", 1, 15)
    
        
 
        
     
     
    
    
       
       #############################################################################################################################################################################
       #################################################################BOTON CAMBIAR TITULAR DEL TERRENO##########################################################################
       ############################################################################################################################################################################


    titulares_cargar_titular_cargados = ""
   
    def cargar_titular_cambiar_titular(self):
        try: 
            sql = 'select * from catastro.titular'
            r = self.driver.read(sql=sql)
        except Exception as ex: 
            print(ex) 
    
            
        list_widget = self.dlg_select_titular_cambio_titular.list_titular
        
        for i in range(list_widget.count()):
        
            list_widget.takeItem(0)
        
        lista = []
                
        for item in r:
            lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))

        # print(lista)
        list_widget.addItems(lista)
        
        self.titulares_cargar_titular_cargados = r    

    def titular_titular_cambiar_busca_ref(self):
        
        list_widget = self.dlg_select_titular_cambio_titular.list_titular
            
        
            
        # features = list(self.titulares_cargados.getFeatures())
        


        
        text_busqueda  = self.dlg_select_titular_cambio_titular_busca_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText()

        try: 
            sql = f'''select * from catastro.titular where documento = '{valor_busqueda}' '''
            r = self.driver.read(sql=sql,multi=False)
            # print(r)
            if r != None:
                item = str(r["id"]) + "    " + str(r["nombre"]) + " " + str(r["apellidos"]) + " " + str(r["documento"])
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                list_widget.addItem(item)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex) 
               
       
    def titular_titular_cambiar_busca_nombre(self):
    
        list_widget = self.dlg_select_titular_cambio_titular.list_titular
        
       

        text_busqueda  = self.dlg_select_titular_cambio_titular_busca_nombre.text_titular
        valor_busqueda = text_busqueda.toPlainText()

        try: 
            
            
            l = valor_busqueda.split()
            valor_busqueda = ''
            for e in l: 
                valor_busqueda  = valor_busqueda + '%' + e + '% '
            print(valor_busqueda)
            sql = f''' select * from catastro.titular 
            where nombre || ' ' ||apellidos ilike '{valor_busqueda[:-1]}' '''
            r = self.driver.read(sql=sql)
            # print(r)
            
            if len(r) > 0 :
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                lista = []
                for item in r:
                    lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))
                
                list_widget.addItems(lista)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex) 

    def cambia_titular(self):    
        
        layer = iface.activeLayer()
        
        features = layer.selectedFeatures()
        
        feature = features[0]
        
        
        list_widget = self.dlg_select_titular_cambio_titular.list_titular
        current = list_widget.currentItem()
        
        #Obtengo el texto del QListWidgetItem
        list_widget_name = current.text()      
        titular_tuple = list_widget_name.split()
           
        id_titular = titular_tuple[0]
        


     

        # print(r)
        sql = f''' UPDATE catastro.terrenos19
            SET  titular= {titular_tuple[-1]}
            WHERE codigo = '{feature["codigo"]}' '''
        # print(sql)
        self.driver.update(sql=sql)
        
         
        
 


        ##########################################################################################################################################################################
        #################################################################BOTON UNIR DOS TERRENOS##############################################################################################################################################
       ##########################################################################################################################################################################
       
    titulares_cargar_union = ""
   
    def cargar_titular_union(self):
    

        try: 
            sql = 'select * from catastro.titular'
            r = self.driver.read(sql=sql)
        except Exception as ex: 
            print(ex) 
    
            
        list_widget = self.dlg_select_titular_union.list_titular
        
        for i in range(list_widget.count()):
        
            list_widget.takeItem(0)
        
        lista = []
                
        for item in r:
            lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))

        # print(lista)
        list_widget.addItems(lista)
        
        self.titulares_cargar_titular_cargados = r  

    def titular_union_busca_ref(self):
        
        list_widget = self.dlg_select_titular_union.list_titular
            
        
        text_busqueda  = self.dlg_select_titular_union_busca_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText()
        

        try: 
            sql = f'''select * from catastro.titular where documento = '{valor_busqueda}' '''
            r = self.driver.read(sql=sql,multi=False)
            # print(r)
            if r != None:
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)

                item = str(r["id"]) + "    " + str(r["nombre"]) + " " + str(r["apellidos"]) + " " + str(r["documento"])
                list_widget.addItem(item)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex) 
    
       
    def titular_union_busca_nombre(self):
    
        list_widget = self.dlg_select_titular_union.list_titular

            
        text_busqueda  = self.dlg_select_titular_union_busca_nombre.text_titular
        valor_busqueda = text_busqueda.toPlainText().lower()

        try: 
            
            
            l = valor_busqueda.split()
            valor_busqueda = ''
            for e in l: 
                valor_busqueda  = valor_busqueda + '%' + e + '% '
            # print(valor_busqueda)
            sql = f''' select * from catastro.titular 
            where nombre || ' ' ||apellidos ilike '{valor_busqueda[:-1]}' '''
            r = self.driver.read(sql=sql)
            # print(r)
            
            if len(r) > 0 :
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                lista = []
                for item in r:
                    lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))
                
                list_widget.addItems(lista)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex)
       
    def union_titular(self):    
        
        layer = iface.activeLayer()
        
        features = layer.selectedFeatures()
        
        feature_primera = features[0]
        feature_segunda = features[1]

        c1 = feature_primera['codigo']
        c2 = feature_segunda['codigo']
        
        geom = None
        for feat in features:
            if geom == None:
                geom = feat.geometry()
            else:
                geom = geom.combine(feat.geometry())

               
        ver = geom.vertexAt(0)
        
        points=[]
        pointsxy = []
        coordenadas = []
        coordenadasArray =[]
        n = 0
        
        while(ver.isEmpty() != True):
            n +=1
            points.append(ver)
            ver=geom.vertexAt(n)
            ver_xy = QgsPointXY(ver)
            # print(ver_xy)
            pointsxy.append(ver_xy)
            x = ver_xy.x()
            y = ver_xy.y()
            coordenadas.append(x)
            coordenadas.append(y)
            
            coordenadasArray.append(ver_xy)
            
            coordenadas = []
        
        coordenadasArray.pop()
        
        primera_coordenada = coordenadasArray[0]
        coordenadasArray.append(primera_coordenada)
        

        dataTerreno_primero = self.driver.read(f''' select * from catastro.terrenos19 where codigo = '{feature_primera["codigo"]}' ''', multi=False )
        # print(dataTerreno_primero)
        
        

       

        dataTerreno_segundo = self.driver.read(f''' select * from catastro.terrenos19 where codigo = '{feature_segunda["codigo"]}' ''', multi=False )
        # print(dataTerreno_segundo)
        
        

        
        list_widget = self.dlg_select_titular_union.list_titular
        current = list_widget.currentItem()
        
        #Obtengo el texto del QListWidgetItem
        list_widget_name = current.text()      
        titular_tuple = list_widget_name.split()
        
        id_titular = titular_tuple[0]
        
        


        agua_union = False
        if dataTerreno_primero['agua'] or dataTerreno_segundo['agua']:
            agua_union = True
        
        alcantarillado_union = False
        if dataTerreno_primero['alcantarillado'] or dataTerreno_segundo['alcantarillado']:
            alcantarillado_union = True
                       
        internet_union = False
        if dataTerreno_primero['internet'] or dataTerreno_segundo['internet']:
            alcantarillado_union = True
            
        energia_union = False
        if dataTerreno_primero['energia'] or dataTerreno_segundo['energia']:
            energia_union = True

        telefono_union = False
        if dataTerreno_primero['telefono'] or dataTerreno_segundo['telefono']:
            telefono_union = True

        transporte_union = False
        if dataTerreno_primero['transporte'] or dataTerreno_segundo['transporte']:
            transporte_union = True
            
        
      
        nuevo_codigo = self.dlg_info_codigo_union.txt_codigo.toPlainText()
        nueva_direccion = self.dlg_info_codigo_union.txt_direccion.toPlainText()
        
        fondo_primero = float(dataTerreno_primero["fondo"])
        fondo_segundo = float(dataTerreno_segundo["fondo"])
        
        fondo_union = 0
        if fondo_primero >= fondo_segundo:
            fondo_union = fondo_primero
        else:
            fondo_union = fondo_segundo
        
        
        frente_primero = float(dataTerreno_primero["frente"])
        frente_segundo = float(dataTerreno_segundo["frente"])
        
        frente_union = frente_primero + frente_segundo
        
        
        suptest_primero = float(dataTerreno_primero["suptest"])
        suptest_segundo = float(dataTerreno_segundo["suptest"])
        
        suptest_union = suptest_primero + suptest_segundo
        
        
        
        superficie_union = dataTerreno_primero["superficie"] + dataTerreno_segundo["superficie"]

                 


        sql = f''' UPDATE catastro.terrenos19 SET 
        codigo='{nuevo_codigo}', 
        direccion='{nueva_direccion}', 
        superficie={superficie_union}, 
        barrio='{dataTerreno_primero["barrio"]}', 
        via={dataTerreno_primero['via']}, 
        agua={agua_union}, 
        alcantarillado={alcantarillado_union}, 
        energia={energia_union}, 
        telefono={telefono_union}, 
        transporte={transporte_union}, 
        internet={internet_union}, 
        titular={id_titular}, 
        topografia={dataTerreno_primero['topografia']}, 
        forma={dataTerreno_primero['forma']}, 
        ubicacion={dataTerreno_primero['ubicacion']}, 
        frente={frente_union}, 
        fondo={fondo_union}, 
        suptest={suptest_union}, 
        manzano='{dataTerreno_primero['manzano']}',
        predio='{dataTerreno_primero['predio']}', 
        subpredio='{dataTerreno_primero['subpredio']}', 
        norte='{dataTerreno_primero['norte']}', 
        sur='{dataTerreno_primero['sur']}', 
        este='{dataTerreno_primero['este']}',
        oeste='{dataTerreno_primero['oeste']}', 
        base='{dataTerreno_primero['base']}', 
        zona={dataTerreno_primero['zona']}, 
        material_via={dataTerreno_primero['material_via']}, 
        geom=src.geom
        from (select st_multi(st_union(geom)) geom from catastro.terrenos19 where codigo in('{dataTerreno_primero['codigo']}','{dataTerreno_segundo['codigo']}')) as src
        WHERE codigo='{dataTerreno_primero['codigo']}';
        '''

        self.driver.update(sql=sql)

        self.driver.delete(f''' delete from catastro.terrenos19 where id = '{dataTerreno_segundo['id']}' ''')
     
        
        
         
       



        ##########################################################################################################################################################################
        #################################################################BOTON DIVIDIR TERRENOS##############################################################################################################################################
       ##########################################################################################################################################################################  
       
       
    terreno_seleccionado_division = "" 
    linea_seleccionada_division = ""
     
       
    def guardar_terreno(self):
        
        layer_terreno = iface.activeLayer()
        
        features = layer_terreno.selectedFeatures()
        
        feature = features[0]
        


        self.terreno_seleccionado_division = feature
        
       

    def guardar_linea(self):
        
        layer_linea_division = iface.activeLayer()
        
        features = layer_linea_division.selectedFeatures()
        
        feature = features[0]
 

        self.linea_seleccionada_division = feature       

    titular1_cargar_division = ""
   
    def cargar_titular_divide1(self):
            
        list_widget = self.dlg_select_titular_divide1.list_titular
        
        try: 
            sql = 'select * from catastro.titular'
            r = self.driver.read(sql=sql)
        except Exception as ex: 
            print(ex) 
            
        for i in range(list_widget.count()):
        
            list_widget.takeItem(0)
        
        lista = []
                
        for item in r:
            lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))

        # print(lista)
        list_widget.addItems(lista)
        
        self.titulares_cargar_titular_cargados = r     

    def titular_divide1_busca_ref(self):
        
        list_widget = self.dlg_select_titular_divide1.list_titular
            
        
        text_busqueda  = self.dlg_select_titular_divide1_buscar_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText()
            

        try: 
            sql = f'''select * from catastro.titular where documento = '{valor_busqueda}' '''
            r = self.driver.read(sql=sql,multi=False)
            # print(r)
            if r != None:
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)

                item = str(r["id"]) + "    " + str(r["nombre"]) + " " + str(r["apellidos"]) + " " + str(r["documento"])
                list_widget.addItem(item)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex) 
      
    def titular_divide1_busca_nombre(self):
    
        list_widget = self.dlg_select_titular_divide1.list_titular
        
    
            
        text_busqueda  = self.dlg_select_titular_divide1_buscar_nombre.text_titular
        valor_busqueda = text_busqueda.toPlainText().lower()
              
       

        try: 
            
            l = valor_busqueda.split()
            valor_busqueda = ''
            for e in l: 
                valor_busqueda  = valor_busqueda + '%' + e + '% '
            # print(valor_busqueda)
            sql = f''' select * from catastro.titular 
            where nombre || ' ' ||apellidos ilike '{valor_busqueda[:-1]}' '''
            r = self.driver.read(sql=sql)
            # print(r)
            
            if len(r) > 0 :
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                lista = []
                for item in r:
                    lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))
                
                list_widget.addItems(lista)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex)
        
    titular2_cargar_division = ""
   
    def cargar_titular_divide2(self):
    

            
        list_widget = self.dlg_select_titular_divide2.list_titular
        
        try: 
            sql = 'select * from catastro.titular'
            r = self.driver.read(sql=sql)
        except Exception as ex: 
            print(ex) 
            
        for i in range(list_widget.count()):
        
            list_widget.takeItem(0)
        
        lista = []
                
        for item in r:
            lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))

        # print(lista)
        list_widget.addItems(lista)
        
        self.titulares_cargar_titular_cargados = r 

    def titular_divide2_busca_ref(self):
        
        list_widget = self.dlg_select_titular_divide2.list_titular
            
        
        text_busqueda  = self.dlg_select_titular_divide2_buscar_ref.text_titular
        valor_busqueda = text_busqueda.toPlainText()
            
  
        try: 
            sql = f'''select * from catastro.titular where documento = '{valor_busqueda}' '''
            r = self.driver.read(sql=sql,multi=False)
            # print(r)
            if r != None:
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)

                item = str(r["id"]) + "    " + str(r["nombre"]) + " " + str(r["apellidos"]) + " " + str(r["documento"])
                list_widget.addItem(item)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex) 
              
    def titular_divide2_busca_nombre(self):
    
        list_widget = self.dlg_select_titular_divide2.list_titular
        
        
            
        text_busqueda  = self.dlg_select_titular_divide2_buscar_nombre.text_titular
        valor_busqueda = text_busqueda.toPlainText().lower()
              
        try: 
            
            l = valor_busqueda.split()
            valor_busqueda = ''
            for e in l: 
                valor_busqueda  = valor_busqueda + '%' + e + '% '
            # print(valor_busqueda)
            sql = f''' select * from catastro.titular 
            where nombre || ' ' ||apellidos ilike '{valor_busqueda[:-1]}' '''
            r = self.driver.read(sql=sql)
            # print(r)
            
            if len(r) > 0 :
                for i in range(list_widget.count()):
                    list_widget.takeItem(0)
                lista = []
                for item in r:
                    lista.append(str(item["id"]) + "    " + str(item["nombre"]) + " " + str(item["apellidos"]) + " " + str(item["documento"]))
                
                list_widget.addItems(lista)
            else: 
                self.driver.showMessage('No existen registros con este Documento, cree un titular.',1,15)
            
            # self.titulares_cargar_titular_cargados = r
        except Exception as ex: 
            print(ex)
               
    def ejes_de_vias(self):
        lyr = self.iface.activeLayer() 
        features = [f for f in lyr.getSelectedFeatures()]
        draw = QgsVectorLayer('LineString?crs=epsg:32719','nuevo_eje_via','memory')
        QgsProject.instance().addMapLayer(draw)
        draw.startEditing()
        self.iface.actionAddFeature().trigger()
        self.iface.setActiveLayer(draw)

        if len(features) == 1:
            feat = features[0]
            sql_direccion = f'''  select distinct direccion from catastro.terrenosvista19 t where manzano = '{feat['manzana']}' '''
            direcciones = [e[0] for e in self.driver.read(sql_direccion, as_dict=False)]
            direcciones.insert(0,'Selecciona un nombre de Calle')
            # print(direcciones)

            self.cod_manzano = feat['manzana']

            self.nombres_calles = direcciones
            
        else:
            pass
        
        draw.featureAdded.connect(self.finish_eje_via)
        # self.commit_changes()
        	  
    def finish_eje_via(self):
        
        self.dlg_ejes_viales.comboBox.clear()
        feature = [f for f in self.iface.activeLayer().getFeatures()][0]
        # geom = feature.geometry().asWkt()
        self.dlg_ejes_viales.lineEdit.setText(str(self.cod_manzano))
        self.dlg_ejes_viales.comboBox.addItems(self.nombres_calles)
        # self.dlg_ejes_viales.geomWkt.emit(geom)
        self.dlg_ejes_viales.show()
        # print(feature)
         
        # print(geom)
        # self.commit_changes()

    def crear_zonas(self):
        self.dlg_guardar_zona.show()
          
    def commit_changes(self):
        self.iface.activeLayer().commitChanges()

    def divide_titular(self):

        #! FALLANDO EL METODO SPLIT        
    
    
        terreno = self.terreno_seleccionado_division
        linea = self.linea_seleccionada_division

        # print(terreno.geometry(),linea.geometry())
        
        
        verTerreno = terreno.geometry().vertexAt(0)
        
        pointsTerreno=[]
        pointsxyTerreno = []
        coordenadasTerreno = []
        coordenadasArrayTerreno = []
        n = 0       
        
        while(verTerreno.isEmpty() != True):
            verTerreno=terreno.geometry().vertexAt(n)
            n +=1
            pointsTerreno.append(verTerreno)
        
            ver_xyTerreno = QgsPointXY(verTerreno)
            pointsxyTerreno.append(ver_xyTerreno)
            xterreno = ver_xyTerreno.x()
            yterreno = ver_xyTerreno.y()
            
            pointTerreno = QgsPointXY(xterreno, yterreno)
            

            coordenadasArrayTerreno.append(pointTerreno)
            
            coordenadasTerreno = []
        
        coordenadasArrayTerreno.pop()
        # print('coordenadasArrayTerreno',coordenadasArrayTerreno)


        geometriaTerreno = QgsGeometry.fromPolygonXY([coordenadasArrayTerreno])
        # print('geometriaTerreno',geometriaTerreno)



        
        ver = linea.geometry().vertexAt(0)
 
        
        points=[]
        pointsxy = []
        coordenadas = []
        coordenadasArray =[]
        n = 0
        
        while(ver.isEmpty() != True):
            ver=linea.geometry().vertexAt(n)
            n +=1
            points.append(ver)

            ver_xy = QgsPointXY(ver)
            
            pointsxy.append(ver_xy)
            x = ver_xy.x()
            y = ver_xy.y()
            
            point = QgsPointXY(x, y)
            # print(ver_xy)
            

            coordenadasArray.append(ver_xy)
            
            # coordenadas = []
        
        # print('coordenadasArray',coordenadasArray)
        coordenadasArray.pop()
        
            
        geometriaLinea = QgsLineString(coordenadasArray)
        # print('geometriaLinea',geometriaLinea)
        
  
      

        

        layerTerreno = QgsVectorLayer("Polygon?crs=32719","terreno","memory")
        provider = layerTerreno.dataProvider()
        layerTerreno.dataProvider().addAttributes([QgsField("id",QVariant.Int)])
        layerTerreno.updateFields()
        
        featureTerreno = QgsFeature()
        featureTerreno.setFields(layerTerreno.fields())
        featureTerreno.setAttribute('id', 1)
        featureTerreno.setGeometry(geometriaTerreno)
        features = []
        features.append(featureTerreno)
        
        layerTerreno.dataProvider().addFeatures(features)
        
        iterator = layerTerreno.getFeatures()
        featuresIterador = list(iterator)
        
        featureIterador = featuresIterador[0]

        # QgsProject.instance().addMapLayer(layerTerreno) #! AGREGAR LAYER TERRENO
        
        

        feats_to_update=[]
        geomIterador = featureIterador.geometry()
        t = geomIterador.reshapeGeometry(geometriaLinea)
        feats_to_update.append([featureIterador.id(),geomIterador])
        
        diff = QgsFeature()
      # Calculate the difference between the original geometry and the first half of the split
        diff.setGeometry( geomIterador.difference(featureIterador.geometry()))
        print('diff',geomIterador)

        layerDif = QgsVectorLayer("Polygon?crs=32719",'diff','memory')
        layerDif.dataProvider().addFeatures(diff)
        QgsProject.instance().addMapLayer(layerDif)

        
        
       
        
        verIzqda = geomIterador.vertexAt(0)

        coordenadasIzqda = []
        coordenadasArrayIzqda =[]
        nIzqda = 0
        
        while(verIzqda.isEmpty() != True):
            
            verIzqda=geomIterador.vertexAt(nIzqda)
      
            xIzqda = verIzqda.x()
            yIzqda = verIzqda.y()
            coordenadasIzqda.append(xIzqda)
            coordenadasIzqda.append(yIzqda)
            
            coordenadasArrayIzqda.append(coordenadasIzqda)
            
            coordenadasIzqda = []
            
            nIzqda +=1
            
        
        coordenadasArrayIzqda.pop()
        # coordenadasArrayIzqda.append(coordenadasArrayIzqda[0])
        print(coordenadasArrayIzqda)

  
        verDerecha = diff.geometry()
        print('verDerecha',verDerecha)

        coordenadasDerecha = []
        coordenadasArrayDerecha =[]
        nDerecha = 0
        
        while(verDerecha.isEmpty() != True):
            
            verDerecha=diff.geometry().vertexAt(nDerecha)
            # print('verDerecha',verDerecha)
      
            xDerecha = verDerecha.x()
            yDerecha = verDerecha.y()
            coordenadasDerecha.append(xDerecha)
            coordenadasDerecha.append(yDerecha)

            print(xDerecha,yDerecha)
            
            coordenadasArrayDerecha.append(coordenadasDerecha)
            
            # coordenadasDerecha = []
            
            nDerecha +=1
            
        print('coordenadasArrayDerecha',coordenadasArrayDerecha)
       
        
      
 

