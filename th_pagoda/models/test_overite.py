from odoo import fields, models, api


class ThCars(models.Model):
    _name = 'th.cars'
    _description = 'For the car'

    name = fields.Char('Name')
    th_engine = fields.Char('Engine')
    th_auto_com_id = fields.Many2one('th.automobile.company', 'Automobile company')
    state = fields.Selection(selection=[('new', "New"), ("like_new", "Like New"), ('old', "Old")], default='new')

    def th_action_create_demo(self):
        vals = {
            'name': self.env['ir.sequence'].next_by_code('car.name'),
            'th_engine': self.env['ir.sequence'].next_by_code('car.engine')

        }
        self.create(vals)

    @api.model
    def create(self, values):
        # Add code here
        return super(ThCars, self).create(values)

    def write(self, values):
        # Add code here
        return super(ThCars, self).write(values)

class AutomobileCompany(models.Model):
    _name = 'th.automobile.company'
    _description = 'For the company'

    name = fields.Char('Name')
    th_logo = fields.Image('Logo')
    th_subsidiaries_ids = fields.One2many('th.subsidiaries', 'th_auto_com_id', 'Subsidiaries')


class Subsidiaries(models.Model):
    _name = 'th.subsidiaries'
    _description = 'For the subsidiaries'

    name = fields.Char('Name')
    th_auto_com_id = fields.Many2one('th.automobile.company', 'Automobile company')

