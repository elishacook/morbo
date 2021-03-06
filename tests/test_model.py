"""
Unit tests for models
"""
import unittest
from morbo import connection, Model
from morbo.validators import *


connection.setup('morbotests')


class TestModel(unittest.TestCase):
    
    def setUp(self):
        for c in connection.database.collection_names():
            try:
                connection.database.drop_collection(c)
            except:
                pass
            
            
    def test_create_simple(self):
        """
        Should be able to create a model with a few simple properties, save it
        and retrieve it by id.
        """
        class Foo(Model):
            name = Text()
            bars = TypeOf(int)
        
        f = Foo()
        f.name = "foo"
        f.bars = 23
        f.save()
        other_f = Foo.find_one(f._id)
        self.assertEqual(other_f, f)
        
        
        
    def test_fail_validation(self):
        """
        Should not be able to save a model with missing or invalid data.
        """
        class Foo(Model):
            name = Text()
            bar = TypeOf(int)
            baz = Text()
            
        f = Foo()
        f.name = "foo"
        f.bar = "7"
        self.assertRaises(InvalidGroupError, f.save)
        
        
    def test_cursor(self):
        """
        Should be able to use the pymongo query interface.
        """
        class Foo(Model):
            name = Text()
            bars = TypeOf(int)
            
        for i in range(0,20):
            f = Foo(name=str(i), bars=i)
            f.save()
        
        self.assertEqual(20, Foo.count())
        
        cur = Foo.find({'bars':{'$gte':10}})
        
        self.assertEqual(10, cur.count())
        
        f = cur.next()
        self.assertIsInstance(f, Foo)
        self.assertEqual(f.name, "10")
        
        cur_copy = cur.clone()
        self.assertEqual(10, cur.count())
        
        foos = list(Foo.find().limit(3))
        self.assertEqual(len(foos), 3)
        
        foos = list(Foo.find().skip(8))
        self.assertEqual(len(foos), 12)
        
        
    def test_remove(self):
        """
        Should be able to remove individual objects from database
        """
        class Foo(Model):
            name = Text()
            bars = TypeOf(int)
            
        f = Foo(name='foo', bars=23)
        f.save()
        
        self.assertEqual(1, Foo.count())
        
        f.remove()
        
        self.assertEqual(0, Foo.count())
        self.assertEqual(f._id, None)
        
        
    def test_find_remove(self):
        """
        Should be able to remove multiple objects using a spec
        """
        class Foo(Model):
            name = Text()
            bars = TypeOf(int)
            
        for i in range(0,20):
            f = Foo(name=str(i), bars=i)
            f.save()
            
        self.assertEqual(20, Foo.count())
        
        Foo.remove({'bars':{'$lt':10}})
        
        self.assertEqual(10, Foo.count())
        
        
    def test_indexing(self):
        class Blubber(Model):
            weight = TypeOf(float)
            volume = TypeOf(float)
            color = Enum('white', 'off-white', 'pinkish', 'tawny')
            indexes = [
                'color',
                [('color', 1), ('weight', -1)]
            ]
        
        q = Blubber.find({'color':'white'}).explain()
        self.assertTrue(q['cursor'].startswith('BtreeCursor'))
        
        q = Blubber.find({'color':'white', 'weight': 23.32}).explain()
        self.assertTrue(q['cursor'].startswith('BtreeCursor'))
        
        q = Blubber.find({'foo':'bar'}).explain()
        self.assertEqual(q['cursor'], 'BasicCursor')
        
        
    def test_hooks(self):
        
        class Snowflake(Model):
            name = Text()
            
            created_flag = False
            modified_flag = False
            
            def was_created(self):
                self.created_flag = True
                
            def was_modified(self):
                self.modified_flag = True
                
        s = Snowflake()
        s.name = 'Fred'
        self.assertFalse(s.created_flag)
        s.save()
        self.assertTrue(s.created_flag)
        
        s.name = 'Tootsie'
        self.assertFalse(s.modified_flag)
        s.save()
        self.assertTrue(s.modified_flag)
        
        
    def test_inheritance(self):
        class Foo(Model):
            name = Text()
            
        class Bar(Foo):
            desc = Text()
        
        self.assertEqual(Foo.collection_name, Bar.collection_name)
        self.assertEqual(Foo.get_collection(), Bar.get_collection())
        
        foo = Foo(name="foo")
        foo.save()
        bar = Bar(name="bar", desc="blah blah blah")
        bar.save()
        
        self.assertEqual(Foo.count(), 2)
        self.assertEqual(Bar.count(), 1)
        
        results = list(Foo.find().sort('name'))
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], Bar)
        self.assertIsInstance(results[1], Foo)
        
        
    def test_str(self):
        class Foo(Model):
            pass
            
        for fn in [str, repr]:
            f = Foo()
            self.assertEqual(fn(f), "<Foo \"unsaved\">")
            f.save()
            self.assertEqual(fn(f), "<Foo \"%s\">" % f._id)
            
            
    def test_validate_empty_string(self):
        class Foo(Model):
            name = Email(optional=True)
            
        
        f1 = Foo(email="")
        try:
            f1.validate()
        except InvalidGroupError:
            self.fail()
            
        f2 = Foo()
        try:
            f2.validate()
        except InvalidGroupError:
            self.fail()


if __name__ == "__main__":
    unittest.main()
