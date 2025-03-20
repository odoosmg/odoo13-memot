# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import math
from odoo.exceptions import Warning


class MaterialPurchaseRequisition(models.Model):
    _name = "material.purchase.requisition"
    _rec_name = 'sequence'
    _order = 'sequence desc'
    _description = "Material Purchase Requisition"
    _inherit = ["mail.thread"]

    # @api.onchange('employee_id')
    # def get_emp_data(self):
    # if self.employee_id:
    # self.destination_location_id = self.employee_id.destination_location_id

    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('material.purchase.requisition') or '/'
        return super(MaterialPurchaseRequisition, self).create(vals)

    @api.model
    def default_get(self, flds):
        result = super(MaterialPurchaseRequisition, self).default_get(flds)
        result['requisition_date'] = datetime.now()
        return result

    def confirm_requisition(self):
        for requisition in self:
            requisition.write({
                'state': 'department_approval',
                'confirmed_by_id': self.env.user.id,
                'confirmed_date': datetime.now()
            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_employee_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.employee_id.work_email
                values['email_to'] = self.requisition_responsible_id.email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def department_approve(self):
        for requisition in self:
            requisition.write({
                'state': 'director_approval',
                'department_manager_id': self.env.user.id,
                'department_approval_date': datetime.now(),
                'director_approval_id': self.director_id.id
            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_manager_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.env.user.partner_id.email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def director_approval(self):
        for requisition in self:
            if self.director_id_1:
                if not self.director_approval_date:
                    requisition.write({
                        'director_approval_id': self.director_id_1.id,
                        'director_approval_date': datetime.now()
                    })
                elif self.director_id_2:
                    if not self.director_approval_date1:
                        requisition.write({
                            'director_approval_id': self.director_id_2.id,
                            'director_approval_date1': datetime.now()
                        })
                    else:
                        requisition.write({
                            'state': 'dmd_approval',
                            'director_approval_id': None,
                            'director_approval_date2': datetime.now()
                        })
                else:
                    requisition.write({
                        'state': 'dmd_approval',
                        'director_approval_id': None,
                        'director_approval_date1': datetime.now()
                    })
            else:
                requisition.write({
                    'state': 'dmd_approval',
                    'director_approval_id': None,
                    'director_approval_date': datetime.now()
                })

            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_manager_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.env.user.partner_id.email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def dmd_approval(self):
        for requisition in self:
            requisition.write({
                'state': 'ir_approve',
                'dmd_approval_id': self.env.user.id,
                'dmd_approval_date': datetime.now()
            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_manager_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.env.user.partner_id.email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def action_cancel(self):
        for requisition in self:
            picking_requisition_ids = self.env['stock.picking'].search([('origin', '=', requisition.sequence)])
            if picking_requisition_ids:
                for req in picking_requisition_ids:
                    req.action_cancel()
                    req.unlink()
            pur_requisition_ids = self.env['purchase.order'].search([('origin', '=', requisition.sequence)])
            if pur_requisition_ids:
                for p_req in pur_requisition_ids:
                    p_req.button_cancel()
                    p_req.unlink()
            requisition.write({'state': 'cancel'})

    def action_received(self):
        for requisition in self:
            requisition.write({
                'state': 'received',
                'received_date': datetime.now()
            })

    def action_reject(self):
        for requisition in self:
            picking_requisition_ids = self.env['stock.picking'].search([('origin', '=', requisition.sequence)])
            if picking_requisition_ids:
                for req in picking_requisition_ids:
                    req.action_cancel()
                    req.unlink()
            pur_requisition_ids = self.env['purchase.order'].search([('origin', '=', requisition.sequence)])
            if pur_requisition_ids:
                for p_req in pur_requisition_ids:
                    p_req.button_cancel()
                    p_req.unlink()
            requisition.write({
                'state': 'cancel',
                'rejected_date': datetime.now(),
                'rejected_by': self.env.user.id
            })

    def reset_requester(self):
        for requisition in self:
            requisition.write({
                'state': 'new',
                'confirmed_by_id': None,
                'confirmed_date': None,
                'department_manager_id': None,
                'department_approval_date': None,
                'director_approval_id': None,
                'director_approval_date': None,
                'director_approval_date1': None,
                'director_approval_date2': None,
                'dmd_approval_id': None,
                'dmd_approval_date': None

            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_manager_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.env.user.partner_id.email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def reset_department(self):
        for requisition in self:
            requisition.write({
                'state': 'department_approval',
                'department_manager_id': None,
                'department_approval_date': None,
                'director_approval_id': None,
                'director_approval_date': None,
                'director_approval_date1': None,
                'director_approval_date2': None,
                'dmd_approval_id': None,
                'dmd_approval_date': None

            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_manager_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.env.user.partner_id.email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def reset_director(self):
        for requisition in self:

            if self.director_id_2:
                cur_direct = self.director_id_2.id
            elif self.director_id_1:
                cur_direct = self.director_id_1.id
            else:
                cur_direct = self.director_id.id

            requisition.write({
                'state': 'director_approval',
                'director_approval_id': cur_direct,
                'director_approval_date': None,
                'director_approval_date1': None,
                'director_approval_date2': None,
                'dmd_approval_id': None,
                'dmd_approval_date': None

            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_manager_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.env.user.partner_id.email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def reset_dmd(self):
        for requisition in self:
            requisition.write({
                'state': 'dmd_approval',
                'dmd_approval_id': None,
                'dmd_approval_date': None

            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_manager_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.env.user.partner_id.email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def action_reset_draft(self):
        for requisition in self:
            picking_requisition_ids = self.env['stock.picking'].search([('origin', '=', requisition.sequence)])
            if picking_requisition_ids:
                for req in picking_requisition_ids:
                    req.action_cancel()
                    req.unlink()
            pur_requisition_ids = self.env['purchase.order'].search([('origin', '=', requisition.sequence)])
            if pur_requisition_ids:
                for p_req in pur_requisition_ids:
                    p_req.button_cancel()
                    p_req.unlink()
            requisition.write({
                'state': 'new',
            })

    def action_move_adviser(self):
        for requisition in self:
            requisition.write({
                'state': 'adviser_approval',

            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_user_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.employee_id.work_email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def action_adviser(self):
        for requisition in self:
            requisition.write({
                'state': 'ir_approve',
                'adviser_approval_id': self.env.user.id,
                'adviser_approval_date': datetime.now()
            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_user_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.employee_id.work_email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def action_approve(self):
        for requisition in self:
            requisition.write({
                'state': 'approved',
                'approved_by_id': self.env.user.id,
                'approved_date': datetime.now()
            })
            template_id = self.env['ir.model.data'].get_object_reference(
                'bi_material_purchase_requisitions',
                'email_user_purchase_requisition')[1]
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            if template_id:
                values = email_template_obj.generate_email(requisition.id, fields=None)
                values['email_from'] = self.employee_id.work_email
                values['email_to'] = self.employee_id.work_email
                values['res_id'] = False
                mail_mail_obj = self.env['mail.mail']
                msg_id = mail_mail_obj.sudo().create(values)
                if msg_id:
                    mail_mail_obj.send([msg_id])

    def create_picking_po(self):
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']
        for requisition in self:
            for line in requisition.requisition_line_ids:
                if line.requisition_action == 'purchase_order':
                    for vendor in line.vendor_id:
                        pur_order = purchase_order_obj.search(
                            [('requisition_po_id', '=', requisition.id), ('partner_id', '=', vendor.id)])
                        if pur_order:
                            po_line_vals = {
                                'product_id': line.product_id.id,
                                'product_qty': line.qty,
                                'name': line.description,
                                'price_unit': line.product_id.list_price,
                                'date_planned': datetime.now(),
                                'product_uom': line.uom_id.id,
                                'order_id': pur_order.id,
                            }
                            purchase_order_line = purchase_order_line_obj.create(po_line_vals)
                        else:
                            vals = {
                                'partner_id': vendor.id,
                                'date_order': datetime.now(),
                                'requisition_po_id': requisition.id,
                                'origin': requisition.sequence,
                                'state': 'draft',
                                'picking_type_id': requisition.picking_type_id.id
                            }
                            purchase_order = purchase_order_obj.create(vals)
                            po_line_vals = {
                                'product_id': line.product_id.id,
                                'product_qty': line.qty,
                                'name': line.description,
                                'price_unit': line.product_id.list_price,
                                'date_planned': datetime.now(),
                                'product_uom': line.uom_id.id,
                                'order_id': purchase_order.id,
                            }
                            purchase_order_line = purchase_order_line_obj.create(po_line_vals)
                else:
                    stock_picking_obj = self.env['stock.picking']
                    stock_move_obj = self.env['stock.move']
                    stock_picking_type_obj = self.env['stock.picking.type']
                    picking_type_id = False

                    if not requisition.use_manual_locations:
                        picking_type_id = requisition.internal_picking_id
                    else:
                        picking_type_id = stock_picking_type_obj.search(
                            [('code', '=', 'internal'), ('company_id', '=', requisition.company_id.id or False)],
                            order="id desc", limit=1)

                        if not picking_type_id:
                            picking_type_id = requisition.internal_picking_id

                    if line.vendor_id:
                        for vendor in line.vendor_id:

                            pur_order = stock_picking_obj.search(
                                [('requisition_picking_id', '=', requisition.id), ('partner_id', '=', vendor.id)])

                            if pur_order:
                                if requisition.use_manual_locations:
                                    pic_line_val = {
                                        'name': line.product_id.name,
                                        'product_id': line.product_id.id,
                                        'product_uom_qty': line.qty,
                                        'picking_id': picking_type_id.id,
                                        'product_uom': line.uom_id.id,
                                        'location_id': requisition.source_location_id.id,
                                        'location_dest_id': requisition.destination_location_id.id,
                                    }
                                else:
                                    pic_line_val = {
                                        'name': line.product_id.name,
                                        'product_id': line.product_id.id,
                                        'product_uom_qty': line.qty,
                                        'picking_id': picking_type_id.id,
                                        'product_uom': line.uom_id.id,
                                        'location_id': picking_type_id.default_location_src_id.id,
                                        'location_dest_id': picking_type_id.default_location_dest_id.id,
                                    }

                                stock_move = stock_move_obj.create(pic_line_val)
                            else:
                                if requisition.use_manual_locations:
                                    val = {
                                        'partner_id': vendor.id,
                                        'location_id': requisition.source_location_id.id,
                                        'location_dest_id': requisition.destination_location_id.id,
                                        'picking_type_id': picking_type_id.id,
                                        'company_id': requisition.env.user.company_id.id,
                                        'requisition_picking_id': requisition.id,
                                        'origin': requisition.sequence,
                                        'location_id': requisition.source_location_id.id,
                                        'location_dest_id': requisition.destination_location_id.id,
                                    }


                                else:

                                    val = {
                                        'partner_id': vendor.id,
                                        'location_id': picking_type_id.default_location_src_id.id,
                                        'location_dest_id': picking_type_id.default_location_src_id.id,
                                        'picking_type_id': picking_type_id.id,
                                        'company_id': requisition.env.user.company_id.id,
                                        'requisition_picking_id': requisition.id,
                                        'location_id': picking_type_id.default_location_src_id.id or vendor.property_stock_supplier.id,
                                        'location_dest_id': picking_type_id.default_location_dest_id.id,
                                        'origin': requisition.sequence
                                    }

                                stock_picking = stock_picking_obj.create(val)
                                if requisition.use_manual_locations:
                                    pic_line_val = {
                                        'partner_id': vendor.id,
                                        'name': line.product_id.name,
                                        'product_id': line.product_id.id,
                                        'product_uom_qty': line.qty,
                                        'product_uom': line.uom_id.id,
                                        'location_id': requisition.source_location_id.id,
                                        'location_dest_id': requisition.destination_location_id.id,
                                        'picking_id': stock_picking.id,
                                        'origin': requisition.sequence

                                    }
                                else:
                                    pic_line_val = {
                                        'partner_id': vendor.id,
                                        'name': line.product_id.name,
                                        'product_id': line.product_id.id,
                                        'product_uom_qty': line.qty,
                                        'product_uom': line.uom_id.id,
                                        'location_id': picking_type_id.default_location_src_id.id or vendor.property_stock_supplier.id,
                                        'location_dest_id': picking_type_id.default_location_dest_id.id,
                                        'picking_id': stock_picking.id,
                                        'origin': requisition.sequence

                                    }
                                stock_move = stock_move_obj.create(pic_line_val)
                    else:
                        pur_order = stock_picking_obj.search([('requisition_picking_id', '=', requisition.id)])

                        if pur_order:
                            if requisition.use_manual_locations:
                                pic_line_val = {
                                    'name': line.product_id.name,
                                    'product_id': line.product_id.id,
                                    'product_uom_qty': line.qty,
                                    'picking_id': stock_picking.id,
                                    'product_uom': line.uom_id.id,
                                    'location_id': requisition.source_location_id.id,
                                    'location_dest_id': requisition.destination_location_id.id,
                                }
                            else:
                                location = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
                                pic_line_val = {
                                    'name': line.product_id.name,
                                    'product_id': line.product_id.id,
                                    'product_uom_qty': line.qty,
                                    'picking_id': stock_picking.id,
                                    'product_uom': line.uom_id.id,
                                    'location_id': picking_type_id.default_location_src_id.id or location.id,
                                    'location_dest_id': picking_type_id.default_location_dest_id.id,
                                }

                            stock_move = stock_move_obj.create(pic_line_val)
                        else:
                            if requisition.use_manual_locations:

                                val = {
                                    'location_id': requisition.source_location_id.id,
                                    'location_dest_id': requisition.destination_location_id.id,
                                    'picking_type_id': picking_type_id.id,
                                    'company_id': requisition.env.user.company_id.id,
                                    'requisition_picking_id': requisition.id,
                                    'origin': requisition.sequence,
                                    'location_id': requisition.source_location_id.id,
                                    'location_dest_id': requisition.destination_location_id.id,
                                }
                            else:

                                location = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
                                val = {
                                    'location_id': picking_type_id.default_location_src_id.id,
                                    'location_dest_id': picking_type_id.default_location_dest_id.id,
                                    'picking_type_id': picking_type_id.id,
                                    'company_id': requisition.env.user.company_id.id,
                                    'requisition_picking_id': requisition.id,
                                    'origin': requisition.sequence,
                                    'location_id': picking_type_id.default_location_src_id.id or location.id,
                                    'location_dest_id': picking_type_id.default_location_dest_id.id,
                                }

                            stock_picking = stock_picking_obj.create(val)
                            if requisition.use_manual_locations:
                                pic_line_val = {
                                    'name': line.product_id.name,
                                    'product_id': line.product_id.id,
                                    'product_uom_qty': line.qty,
                                    'product_uom': line.uom_id.id,
                                    'location_id': requisition.source_location_id.id,
                                    'location_dest_id': requisition.destination_location_id.id,
                                    'picking_id': stock_picking.id,
                                    'origin': requisition.sequence

                                }
                            else:
                                location = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
                                pic_line_val = {
                                    'name': line.product_id.name,
                                    'product_id': line.product_id.id,
                                    'product_uom_qty': line.qty,
                                    'product_uom': line.uom_id.id,
                                    'location_id': picking_type_id.default_location_src_id.id or location.id,
                                    'location_dest_id': picking_type_id.default_location_dest_id.id,
                                    'picking_id': stock_picking.id,
                                    'origin': requisition.sequence

                                }
                            stock_move = stock_move_obj.create(pic_line_val)
            requisition.write({
                'state': 'po_created',
            })

    def _get_internal_picking_count(self):
        for picking in self:
            picking_ids = self.env['stock.picking'].search([('requisition_picking_id', '=', picking.id)])
            picking.internal_picking_count = len(picking_ids)

    def internal_picking_button(self):
        self.ensure_one()
        return {
            'name': 'Internal Picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_picking_id', '=', self.id)],
        }

    def _get_purchase_order_count(self):
        for po in self:
            po_ids = self.env['purchase.order'].search([('requisition_po_id', '=', po.id)])
            po.purchase_order_count = len(po_ids)

    def purchase_order_button(self):
        self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_po_id', '=', self.id)],
        }

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    @api.model
    def _default_picking_internal_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    def _compute_line_amount(self):
        for rec in self:
            total_amount = 0.0
            for line in rec.requisition_line_ids:
                if line.amount:
                    total_amount += line.amount
            rec.total_amount = total_amount

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    @api.depends('employee_id')
    def _get_department_id(self):
        dept_frec = self.env['hr.department'].search([('member_ids.user_id', '=', self.env.uid)], limit=1)
        return dept_frec.id

    def _get_requisition_group(self):
        req_user = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        manager = self.env['res.users'].search([('id', '=', req_user.department_id.manager_id.user_id.id)], limit=1)
        if manager:
            return manager

    @api.depends('employee_id')
    def _get_current_user(self):
        self.current_user = (self.env.user.id == self.employee_id.user_id.id)

        # for rec in self:
        #     if rec.employee_id.user_id.id == self.env.user.id
        #         rec.current_user = True
        #     else
        #         rec.current_user = False

    def _get_current_director(self):
        self.cur_director = (self.env.user.id == self.director_approval_id.id)

    @api.onchange("department_id")
    def _change_department_id(self):
        # dept_frec = self.env['hr.department'].search([('id', '=', self.department_id.id)], limit=1)
        # if dept_frec:
        self.requisition_responsible_id = self.department_id.dept_check_id.id
        self.director_id = self.department_id.director_id.id

    def _get_director_group(self):
        return [("groups_id", "=",
                 self.env.ref("bi_material_purchase_requisitions.group_purchase_requisition_director").id)]

    @api.onchange("director_id")
    def _change_director_id(self):
        self.director_id_1 = None
        return {'domain': {'director_id_1': ['&', '&', ('id', 'not in', [self.director_id_2.id]),
                                             ('id', 'not in', [self.director_id.id]), ("groups_id", "=",
                                                                                       self.env.ref(
                                                                                           "bi_material_purchase_requisitions.group_purchase_requisition_director").id)],
                           'director_id_2': ['&', '&', ('id', 'not in', [self.director_id_1.id]),
                                             ('id', 'not in', [self.director_id.id]), ("groups_id", "=",
                                                                                       self.env.ref(
                                                                                           "bi_material_purchase_requisitions.group_purchase_requisition_director").id)]}}

    @api.onchange("director_id_1")
    def _change_director_id_1(self):
        self.director_id_2 = None
        return {'domain': {'director_id': ['&', '&', ('id', 'not in', [self.director_id_1.id]),
                                           ('id', 'not in', [self.director_id_2.id]), ("groups_id", "=",
                                                                                       self.env.ref(
                                                                                           "bi_material_purchase_requisitions.group_purchase_requisition_director").id)],
                           'director_id_2': ['&', '&', ('id', 'not in', [self.director_id_1.id]),
                                             ('id', 'not in', [self.director_id.id]), ("groups_id", "=",
                                                                                       self.env.ref(
                                                                                           "bi_material_purchase_requisitions.group_purchase_requisition_director").id)]}}

    @api.onchange("director_id_2")
    def _change_director_id_2(self):
        return {'domain': {'director_id': ['&', '&', ('id', 'not in', [self.director_id_2.id]),
                                           ('id', 'not in', [self.director_id_1.id]), ("groups_id", "=",
                                                                                       self.env.ref(
                                                                                           "bi_material_purchase_requisitions.group_purchase_requisition_director").id)],
                           'director_id_1': ['&', '&', ('id', 'not in', [self.director_id_2.id]),
                                             ('id', 'not in', [self.director_id.id]), ("groups_id", "=",
                                                                                       self.env.ref(
                                                                                           "bi_material_purchase_requisitions.group_purchase_requisition_director").id)]}}

    @api.depends('is_group_system')
    def get_user(self):
        res_user = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if res_user.has_group('base.group_system'):
            self.is_group_system = True
        else:
            self.is_group_system = False

    sequence = fields.Char(string='Sequence', readonly=True, copy=False, tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, default=_get_employee_id)
    subject = fields.Char(string="Subject", required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True, default=_get_department_id)
    requisition_responsible_id = fields.Many2one('res.users', string="Requesition Responsible",
                                                 default=_get_requisition_group, required=True)
    requisition_date = fields.Date(string="Requisition Date", required=True)
    received_date = fields.Date(string="Received Date", readonly=True)
    requisition_deadline_date = fields.Date(string="Requisition Deadline")
    current_user = fields.Boolean('is current user ?', compute='_get_current_user')
    cur_director = fields.Boolean('is current director 1 ?', compute='_get_current_director')
    is_group_system = fields.Boolean(string="Administration Setting", compute='get_user')

    state = fields.Selection([
        ('new', 'Requester'),
        ('department_approval', 'Department Check'),
        ('director_approval', 'Director Check'),
        ('dmd_approval', 'DMD Check'),
        ('ir_approve', 'MD Approval'),
        ('adviser_approval', 'Adviser'),
        ('approved', 'Approved'),
        # ('po_created','Purchase Order Created'),
        # ('received','Received'),
        ('cancel', 'Reject')], string='Stage', default="new", tracking=True)
    requisition_line_ids = fields.One2many('requisition.line', 'requisition_id', string="Requisition Line ID")
    confirmed_by_id = fields.Many2one('res.users', string="Confirmed By", copy=False)
    department_manager_id = fields.Many2one('res.users', string="Department Manager", copy=False)
    approved_by_id = fields.Many2one('res.users', string="Approved By", copy=False)
    rejected_by = fields.Many2one('res.users', string="Rejected By", copy=False)
    confirmed_date = fields.Date(string="Confirmed Date", readonly=True, copy=False)
    department_approval_date = fields.Date(string="Department Approval Date", readonly=True, copy=False)
    approved_date = fields.Date(string="MD Approved Date", readonly=True, copy=False)
    rejected_date = fields.Date(string="Rejected Date", readonly=True, copy=False)
    reason_for_requisition = fields.Text(string="Description (English)", required=True)
    reason_for_requisition_kh = fields.Text(string="Description (Khmer)")

    comment_director1 = fields.Text(string="1st Director Comment", tracking=True)
    comment_director2 = fields.Text(string="2nd Director Comment", tracking=True)
    comment_dmd = fields.Text(string="DMD Comment", tracking=True)
    comment_md = fields.Text(string="MD Comment", tracking=True)

    source_location_id = fields.Many2one('stock.location', string="Source Location")
    destination_location_id = fields.Many2one('stock.location', string="Destination Location")
    internal_picking_id = fields.Many2one('stock.picking.type', string="Internal Picking Type",
                                          default=lambda self: self._default_picking_internal_type())
    internal_picking_count = fields.Integer('Internal Picking Count', compute='_get_internal_picking_count')
    purchase_order_count = fields.Integer('Purchase Order', compute='_get_purchase_order_count')
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    picking_type_id = fields.Many2one('stock.picking.type', 'Purchase Operation Type', required=True,
                                      default=lambda self: self._default_picking_type())
    use_manual_locations = fields.Boolean(string="Select Manual Locations")
    total_amount = fields.Float(string='Total Amount', compute='_compute_line_amount')

    director_id = fields.Many2one('res.users', string="1st Director", required=True,
                                  domain=_get_director_group)
    director_approval_date = fields.Date(string="1st Director Check Date", readonly=True, copy=False)

    director_id_1 = fields.Many2one('res.users', string="2nd Director", domain=_get_director_group)
    director_approval_date1 = fields.Date(string="2nd Director Check Date", readonly=True, copy=False)
    director_id_2 = fields.Many2one('res.users', string="3rd Director", domain=_get_director_group)
    director_approval_date2 = fields.Date(string="3rd Director Check Date", readonly=True, copy=False)

    director_approval_id = fields.Many2one('res.users', string="Current Director", copy=False, tracking=True)

    adviser_approval_id = fields.Many2one('res.users', string="Adviser", copy=False)
    dmd_approval_id = fields.Many2one('res.users', string="DMD", copy=False)

    dmd_approval_date = fields.Date(string="DMD Check Date", readonly=True, copy=False)
    adviser_approval_date = fields.Date(string="Adviser Check Date", readonly=True, copy=False)
    request_type = fields.Selection([
        ('purchase', 'Purchase Request: សំណើសុំទិញ'),
        ('itemusage', 'Item Usage Request: សំណើសុំសម្ភារ:ប្រើប្រាស់'),
        ('payment', 'Payment Request: សំណើសុំទូទាត់'),
        ('general', 'General Request or Request for approval: របាយការណ៍ ឬសំណើសុំគោលការណ៍'),
        ('leave', 'Leave Request: លិខិតសុំឈប់សម្រាក'),
        ('resign','Resign Letter: លិខិតសុំលាឈប់ពីការងារ'),
        ('warning','Warning Letter: លិខិតព្រមាន / ដាក់ពិន័យការងារ'),
        ('termination','Termination Letter: លិខិតបញ្ឈប់ពីការងារ'),
        ('change','Change / Promote / Demote: សំណើសុំផ្លាស់ប្តូរតួនាទី / តម្លើងឋានៈ / សម្រួលភារកិច្ច'),
        ('destroy','Delete & Replace: សំណើសុំលុបឈ្មោះ និងជ្រើសរើសជំនួស'),
        ('accident','Accident Report: របាយការណ៍គ្រោះថ្នាក់ / ឧបទ្ទវហេតុ'),
        ('asset','Asset (tree, construction) / ទ្រព្យសកម្ម'),
        ('legal','Legal Procedure (Stealing, Destroying) / ការលួចលាក់, ការបំផ្លិចបំផ្លាញ'),
        ('other','Others: ផ្សេងៗ')], string='Request Type', default="purchase", required=True, tracking=True)
    active = fields.Boolean('Active', default=True)

class RequisitionLine(models.Model):
    _name = "requisition.line"
    _description = "Requisition Line"

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name

    @api.depends('qty', 'price')
    def _onchange_qty(self):
        for line in self:
            line.amount = line.qty * line.price

    product_id = fields.Many2one('product.product', string="Product", domain="[('type','not in',['service'])]")
    description = fields.Text(string="Description")
    qty = fields.Float(string="Quantity", default=1.0)
    uom_id = fields.Many2one('uom.uom', string="Unit Of Measure")
    price = fields.Float(string='Unit price', default=0.00, digits=dp.get_precision('decimal4digit'))
    amount = fields.Float("Extended Cost", readonly=True, store=True, digits=dp.get_precision('decimal4digit'),
                          compute='_onchange_qty')
    requisition_id = fields.Many2one('material.purchase.requisition', string="Requisition Line")
    requisition_action = fields.Selection(
        [('purchase_order', 'Purchase Order'), ('internal_picking', 'Internal Picking')], string="Requisition Action",
        default='purchase_order')
    vendor_id = fields.Many2many('res.partner', string="Vendors")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    requisition_picking_id = fields.Many2one('material.purchase.requisition', string="Purchase Requisition")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    requisition_po_id = fields.Many2one('material.purchase.requisition', string="Purchase Requisition")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # destination_location_id = fields.Many2one('stock.location',string="Destination Location")


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    def _get_department_check_group(self):
        return [("groups_id", "=",
                 self.env.ref("bi_material_purchase_requisitions.group_requisition_department_manager").id)]

    def _get_director_group(self):
        return [("groups_id", "=",
                 self.env.ref("bi_material_purchase_requisitions.group_purchase_requisition_director").id)]

    dept_check_id = fields.Many2one('res.users', string="Department Check", domain=_get_department_check_group)
    director_id = fields.Many2one('res.users', string="Director", domain=_get_director_group)
    destination_location_id = fields.Many2one('stock.location', string="Destination Location")
