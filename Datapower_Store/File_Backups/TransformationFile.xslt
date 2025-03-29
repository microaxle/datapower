<?xml version="1.0" ?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
   <xsl:output method="xml" indent="yes" /> 
   <xsl:template match="/">
      <table>
         <xsl:apply-templates select="/customers/customer/orders/order" /> 
      </table>
   </xsl:template>
   <xsl:template match="order">
      <xsl:variable name="id" select="../../@id" /> 
      <xsl:apply-templates select="/customers/customer/addresses/address[../../@id =$id]">
         <xsl:with-param name="id" select="$id" /> 
         <xsl:with-param name="order_no" select="@order_no" /> 
      </xsl:apply-templates>
   </xsl:template>
   <xsl:template match="address">
      <xsl:param name="id" /> 
      <xsl:param name="order_no" /> 
      <row>
         <column name="CUSTOMER_ID">
            <xsl:value-of select="$id" /> 
         </column>
         <column name="ORDER_NO">
            <xsl:value-of select="$order_no" /> 
         </column>
         <column name="STREET">
            <xsl:value-of select="@street" /> 
         </column>
         <column name="CITY">
            <xsl:value-of select="@city" /> 
         </column>
         <column name="STATE">
            <xsl:value-of select="@state" /> 
         </column>
         <column name="ZIP">
            <xsl:value-of select="@zip" /> 
         </column>
      </row>
   </xsl:template>
</xsl:stylesheet>