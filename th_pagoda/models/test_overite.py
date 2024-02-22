from odoo import fields, models, api


class ThCars(models.Model):
    _name = 'th.cars'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'For the car'

    name = fields.Char('Name', tracking=True)
    th_engine = fields.Char('Engine')
    th_auto_com_id = fields.Many2one('th.automobile.company', 'Automobile company')
    state = fields.Selection(selection=[('new', "New"), ("like_new", "Like New"), ('old', "Old")], default='new')
    th_country_ids = fields.Many2many('th.country')

    def th_action_create_demo(self):
        ###
        # overwrite
        # (0,0 {data})
        th_auto_com_id = (0, 0, {'name': 'Tesla',
                                 'th_subsidiaries_ids': [
                                     (0, 0, {'name': 'SpaceX'}),
                                     (0, 0, {'name': 'Neuralink'})]
                                 })

        vals = {
            'name': self.env['ir.sequence'].next_by_code('car.name'),
            'th_engine': self.env['ir.sequence'].next_by_code('car.engine'),
            'th_auto_com_id': th_auto_com_id
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
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'For the company'

    name = fields.Char('Name')
    th_logo = fields.Image('Logo')
    th_subsidiaries_ids = fields.One2many('th.subsidiaries', 'th_auto_com_id', 'Subsidiaries')

    def th_action_create_demo(self):
        ###
        # overwrite

        # Tạo mới giá trị con
        # vals = {'name': 'Tesla',
        #         'th_subsidiaries_ids': [
        #             (0, 0, {'name': 'SpaceX'}),
        #             (0, 0, {'name': 'Neuralink'})]
        #         }

        # Chỉnh sửa giá trị con
        # vals = {'name': 'Tesla1',
        #         'th_subsidiaries_ids': [(1, 1, {'name': 'Twitter'})]
        #         }

        # Chỉnh sửa giá trị con
        vals = {
            'th_subsidiaries_ids': [(6, 0, [2, 3, 4])]
        }
        vals1 = {'th_subsidiaries_ids': ([(0, 0, {'name': 'SpaceX1'}),
                                          (0, 0, {'name': 'Twitter1'})
                                          ])
                 }

        self.search([('id', '=', 5)]).write(vals)
        self.create(vals1)


class Subsidiaries(models.Model):
    _name = 'th.subsidiaries'
    _description = 'For the subsidiaries'

    name = fields.Char('Name')
    th_auto_com_id = fields.Many2one('th.automobile.company', 'Automobile company')


class Country(models.Model):
    _name = 'th.country'
    _description = 'Country of the car'

    name = fields.Char('Name')
    th_flag = fields.Image('National flag')
    th_car_ids = fields.Many2many('th.cars')
